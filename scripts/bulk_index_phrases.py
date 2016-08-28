import sys
import elasticsearch as es
import elasticsearch.helpers


PHRASE_TYPE = 'phrase'
PHRASE_INDEX = 'phrase'


def generate_phrases(path, min_freq):
    with open(path) as f:
        for line in f:
            freq_str, phrase, tags = line.strip().split('\t')
            freq = int(freq_str)
            if freq >= min_freq:
                obj = {
                        '_op_type': 'index',
                        '_index': PHRASE_INDEX,
                        '_type': PHRASE_TYPE,
                        '_source': {
                            'phrase': phrase,
                            'freq': freq,
                            'tags': tags,
                            }
                        }
                yield obj


def set_mapping(client):
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
        c.create(PHRASE_INDEX, body=settings)

        obj = {
                'properties': {
                    'phrase': {
                        'type':      'string',
                        'analyzer':  'my_english'
                        },
                    'freq': {
                        'type':      'integer',
                        },
                    'tags': {
                        'type':      'string',
                        'index':  'not_analyzed'
                        }
                    }
                }
        c.put_mapping(doc_type=PHRASE_TYPE, index=PHRASE_INDEX, body=obj)

    except Exception as e:
        print('Index already exists: ' + PHRASE_INDEX, file=sys.stderr)


def main(args):
    client = es.Elasticsearch(args.host)
    set_mapping(client)
    g = generate_phrases(args.phrases, args.min)
    for ok, item in es.helpers.streaming_bulk(client, g):
        if not ok:
            print(item, file=sys.stderr)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Index phrases using bulk API.')
    parser.add_argument('host', help='Elasticsearch host')
    parser.add_argument('phrases', help='list of phrases')
    parser.add_argument('--min', default=1, help='minimum frequency')

    main(parser.parse_args())
