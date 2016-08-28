import sys
import bs4
from collections import defaultdict
from multiprocessing import Pool


TAGS = {'V', 'N', 'J', 'I', 'T', 'D', 'R', 'M', 'C', 'H'}
ROOT_TAGS = ['V', 'N', 'J']
CONTENT_TAGS = ['V', 'N', 'J', 'R', 'M']


def extract_dep_tree(sen, d, max_size=5):
    for idx in range(len(sen)):
        lst = []
        while True:
            w, tag, head, dep = sen[idx]
            if tag[0] not in TAGS:
                break
            lst.append((idx, w, tag))
            if head == idx:
                break
            else:
                if dep == 'nsubj':
                    # discard subjects
                    break
                idx = head
            content_len = len(list(filter(lambda t: t[2][0] in CONTENT_TAGS, lst)))   # non-tags
            if tag[0] in ROOT_TAGS and 2 <= content_len <= max_size:
                lst.sort()
                pos_lst = []
                phrase = []
                for _, w, tag in lst:
                    pos_lst.append(tag[0])
                    phrase.append(w)
                if phrase[0] != '-' and phrase[-1] != '-':
                    d[(tuple(phrase), tuple(pos_lst))] += 1


def extract_ngram(sen, d, max_size=10):
    for idx in range(len(sen)):
        lst = []
        pos_lst = []
        phrase = []
        content_len = 0
        for j in range(max_size):
            if idx + j < len(sen):
                w, tag, head, dep = sen[idx+j]
                if tag[0] not in TAGS:
                    break
                pos_lst.append(tag[0])
                phrase.append(w)
                lst.append((w, tag))
                if tag[1][0] in CONTENT_TAGS:
                    content_len += 1
                if content_len >= 2 and phrase[0] != '-' and phrase[-1] != '-':
                    d[(tuple(phrase), tuple(pos_lst))] += 1


def extract_phrases_from_xml(path, use_dep, n, suffix):
    d = defaultdict(int)
    try:
        print('Processing: ' + path, file=sys.stderr)
        with open(path, encoding='utf-8') as f:
            soup = bs4.BeautifulSoup(f, features='html.parser')
            t_paper = soup.find('paper')
            for t_section in soup.find_all('section'):
                for t_sentence in t_section.find_all('sentence'):
                    sen = []
                    for t_token in t_sentence.find_all('token'):
                        form = t_token.form.string
                        lemma = t_token.lemma.string
                        tag = t_token.tag.string
                        if tag == 'VBN' or tag == 'VBG':
                            # convert {present,past}-participle into adjective
                            tag = 'JJ'
                        if tag[0] == 'N':
                            # noun
                            w = form
                            if not (tag == 'NNP' or tag == 'NNPS'):
                                # not proper noun
                                w = w.lower()
                        elif tag[0] == 'J':
                            # adjective
                            w = form
                        else:
                            w = lemma
                        head = int(t_token.head.string)
                        dep = t_token.dep.string
                        tok = (w, tag, head, dep)
                        sen.append(tok)

                    if use_dep:
                        extract_dep_tree(sen, d, n)
                    else:
                        extract_ngram(sen, d, n)

        out_path = path + '.' + suffix
        with open(out_path, 'w', encoding='utf-8') as f:
            for (k, p), v in d.items():
                print('{}\t{}\t{}'.format(v, ' '.join(k), ''.join(p)), file=f)

    except Exception as e:
        print(str(e), file=sys.stderr)
        print('Failed to process: ' + path, file=sys.stderr)


def extract_phrases(paths, dep, n, suffix):
    p = Pool()
    for path in paths:
        p.apply_async(extract_phrases_from_xml, (path, dep, n, suffix))
    p.close()
    p.join()


def main(args):
    extract_phrases(args.data, args.dep, args.n, args.suffix)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Extract phrases from XML files.')
    parser.add_argument('data', nargs='+', help='XML files')
    parser.add_argument('--suffix', default='phrases', help='suffix for generated files')
    parser.add_argument('--n', default=10, type=int, help='max phrase length')
    parser.add_argument('--dep', action='store_true', help='extract phrases based on dependency trees (default: n-grams)')

    main(parser.parse_args())
