import sys
import os
import bs4
import re
import json


CONFERENCE_NAMES = {
    'J': 'CL',
    'Q': 'TACL',
    'P': 'ACL',
    'E': 'EACL',
    'N': 'NAACL',
    'D': 'EMNLP',   # TODO
    'K': 'CoNLL',   # TODO
    'S': 'SemEval',
    'A': 'ANLP',
    'W': 'Workshop',    # TODO
}


RE_SPACES = re.compile(r'\s+')


def process_xml(path):
    with open(path, encoding='utf-8') as f:
        soup = bs4.BeautifulSoup(f, features='html.parser')

        t_volume = soup.find('volume')
        conf_id = t_volume['id']
        conf_key = conf_id[0]
        conference = CONFERENCE_NAMES[conf_key]
        year = int(conf_id[1:])
        if year < 50:
            year += 2000
        else:
            year += 1900

        for t_paper in t_volume.find_all('paper'):
            t_title = t_paper.find('title')
            if not (t_title and t_title.string):
                continue
            title = t_title.string
            title = title.replace('\n', ' ')
            title = RE_SPACES.sub(' ', title)
            title = title.strip()
            names = []
            for t_author in t_paper.find_all('author'):
                try:
                    if t_author.find('first'):
                        es = []
                        for t in t_author:
                            if t.string:
                                e = t.string.strip()
                                if len(e) > 0:
                                    es.append(e)
                        name = ' '.join(es)
                    else:
                        name = t_author.string.strip()
                except Exception as e:
                    print(e, file=sys.stderr)
                    print(t_paper, file=sys.stderr)
                    print(file=sys.stderr)
                    continue
                if len(name) > 0:
                    names.append(name)
            authors = '+'.join(names)
            paper_id = conf_id + '-' + t_paper['id']
            #url = 'http://aclweb.org/anthology/' + conf_key + '/' + conf_id + '/' + paper_id + '.pdf'
            url = 'http://aclweb.org/anthology/' + paper_id

            yield paper_id, title, authors, year, conference, url


def main(args):
    pk = 1
    objs = []
    for dirpath, dirnames, filenames in os.walk(args.dir):
        for filename in filenames:
            if filename.endswith('.xml'):
                for paper_id, title, authors, year, conference, url in process_xml(os.path.join(dirpath, filename)):
                    obj = {
                        'model': 'acl_search.paper',
                        'pk': pk,
                        'fields': {
                            'paper_id': paper_id,
                            'title': title,
                            'authors': authors,
                            'year': year,
                            'conference': conference,
                            'url': url,
                        }
                    }
                    pk += 1
                    objs.append(obj)
    print(json.dumps(objs, indent=2))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Create fixture for meta information of papers.')
    parser.add_argument('dir', help='Meta info directory')

    main(parser.parse_args())
