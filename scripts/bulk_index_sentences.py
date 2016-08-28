import sys
import bs4
import elasticsearch as es
import elasticsearch.helpers
from multiprocessing import Pool
import random

import xml.sax.saxutils

SENTENCE_TYPE = 'sentence'

UNESCAPE = {
    '&quot;': '"',
    '&apos;': '\'',
}


def generate_sentences_for_paper(path, index_name):
    with open(path, encoding='utf-8') as f:
        soup = bs4.BeautifulSoup(f, features='html.parser')

        t_paper = soup.find('paper')
        conf_id = t_paper['conference_id']
        paper_id = t_paper['paper_id']
        paper_id_str = conf_id + '_' + paper_id

        last_section_num = None
        section_offset = -1
        section_name = ''
        for t_section in soup.find_all('section'):
            # get section name
            section_num = t_section['num'] if 'num' in t_section.attrs else ''
            if last_section_num is not None and last_section_num != '' and section_num.startswith(last_section_num):
                # don't update section name
                section_num = last_section_num
            else:
                section_name = xml.sax.saxutils.unescape(t_section['title'], UNESCAPE)
                section_offset += 1
            last_section_num = section_num

            # extract sentences
            for i, t_sentence in enumerate(t_section.find_all('sentence')):
                #sen = []
                #for t_token in t_sentence.find_all('token'):
                #    sen.append(t_token.form.string)
                #sen_str = ' '.join(sen)
                sen_str = xml.sax.saxutils.unescape(t_sentence['raw'], UNESCAPE)

                obj = {
                        '_op_type': 'index',
                        '_index': index_name,
                        '_type': SENTENCE_TYPE,
                        '_source': {
                            'paper': paper_id_str,
                            'section': section_name,
                            'section_num': section_num,
                            'section_offset': section_offset,
                            'offset': i,
                            'body': sen_str,
                            }
                        }
                yield obj


def generate_sentences(paths, index_name):
    total = len(paths)
    for i, path in enumerate(paths):
        try:
            print('Processing [{}/{}]: {}'.format(i+1, total, path), file=sys.stderr)
            for sen in generate_sentences_for_paper(path, index_name):
                yield sen
        except Exception as e:
            print(str(e), file=sys.stderr)
            print('Failed to process: ' + path, file=sys.stderr)
            continue


def set_analyzer(client, index_name):
    c = es.client.IndicesClient(client)
    try:
        settings = {
            'settings': {
                'analysis': {
                    'analyzer': {
                        'my_english': {
                            'type': 'english',
                            'stopwords': '_none_',
                        }
                    }
                }
            }
        }
        c.create(index_name, body=settings)

        obj = {
            "properties": {
                "paper": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "body": {
                    "type": "string",
                    "analyzer": "my_english"
                },
                "section": {
                    "type": "string",
                    "analyzer": "my_english",
                    "fields": {
                        "raw": {
                            "type": "string",
                            "index": "not_analyzed"
                        }
                    }
                },
                "section_num": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "section_offset": {
                    "type": "integer",
                },
                "offset": {
                    "type": "integer",
                },
            }
        }
        c.put_mapping(doc_type=SENTENCE_TYPE, body=obj, index=index_name)

    except Exception as e:
        print('Index already exists: ' + index_name, file=sys.stderr)


def f(host, index, data):
    client = es.Elasticsearch(host)
    g = generate_sentences(data, index)
    for ok, item in es.helpers.streaming_bulk(client, g):
        if not ok:
            print(item, file=sys.stderr)


def main(args):
    client = es.Elasticsearch(args.host)
    set_analyzer(client, args.index)
    p = Pool(processes=args.processes)
    size_per_process = len(args.data) // args.processes + 1
    random.shuffle(args.data)
    for i in range(args.processes):
        paths_for_process = args.data[size_per_process*i:size_per_process*(i+1)]
        p.apply_async(f, (args.host, args.index, paths_for_process))
    p.close()
    p.join()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Index sentences using bulk API.')
    parser.add_argument('host', help='Elasticsearch host')
    parser.add_argument('index', help='index name')
    parser.add_argument('data', nargs='+', help='XML files')
    parser.add_argument('--processes', type=int, default=1, help='number of processes')

    main(parser.parse_args())
