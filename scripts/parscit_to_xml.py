import sys
import os
import bs4
import spacy


def strip_and_one_line(string):
    return string.strip().replace('\n', ' ')
_s = strip_and_one_line


def parse_xml(path):
    with open(path, encoding='utf-8') as f:
        soup = bs4.BeautifulSoup(f, features='html.parser')

        title = None
        authors = None
        affiliations = None

        sections = []
        current_section = None
        current_section_num = None
        current_contents = []
        for t in soup.find('algorithm', {'name': 'SectLabel'}).descendants:
            if type(t) == bs4.element.Tag:
                if t.name == 'variant':
                    title = _s(t.find('title').string) if t.find('title') else ''
                    authors = list(map(lambda t: _s(t.string), t.find_all('author')))
                    affiliations = list(map(lambda t: _s(t.string), t.find_all('affiliation')))
                elif 'sectionheader' in t.name:
                    if t.has_attr('genericheader') and t['genericheader'] == 'references':
                        # reached references
                        break
                    else:
                        # section start
                        if current_section is not None:
                            sections.append((current_section, current_section_num, current_contents))
                        current_section = _s(t.string)
                        if current_section[0].isdigit():
                            es = current_section.split(' ', 1)
                            if len(es) == 2:
                                current_section_num, current_section = es
                            else:
                                current_section_num = None
                        else:
                            current_section_num = None
                        current_contents = []
                elif t.name == 'bodytext':
                    current_contents.append(t.string)
        if current_section is not None:
            sections.append((current_section, current_section_num, current_contents))
        references = []
        for t in soup.find_all('citation'):
            if all([t.authors, t.title, t.date, t.booktitle]):
                # conference proceedings
                ref_authors = []
                for t_a in t.authors.find_all('author'):
                    ref_authors.append(t_a.string)
                ref_title = t.title.string if t.title else ''
                ref_date = t.date.string if t.date else ''
                ref_booktitle = t.booktitle.string if t.booktitle else ''
                references.append((ref_authors, ref_title, ref_date, ref_booktitle))

    return title, authors, affiliations, sections, references


def parse_sentences(nlp, text):
    text = text.strip()
    text = text.replace('\n', ' ')
    text = text.replace('- ', '')
    doc = nlp(text)
    return doc


def filter_malformed_sections(sections):
    res = []
    nums = list(map(lambda t: t[1], sections))
    for i, num in enumerate(nums):
        if 0 < i < len(sections) - 1:
            if nums[i-1] and not num and nums[i+1]:
                # filter out non-numbered sections
                continue
        res.append(sections[i])
    return res


def main(args):
    nlp = spacy.load('en')

    for path in args.data:
        try:
            # extract info
            conference_id, paper_id = os.path.basename(path).split('-')[:2]
            title, authors, affiliations, sections, references = parse_xml(path)

            sections = filter_malformed_sections(sections)

            # construct XML tree
            soup = bs4.BeautifulSoup(features='html.parser')

            t_paper = soup.new_tag('paper')
            t_paper['conference_id'] = conference_id
            t_paper['paper_id'] = paper_id

            t_sections = soup.new_tag('sections')
            for title, section_num, contents in sections:
                t_section = soup.new_tag('section', title=title)
                if section_num:
                    t_section['num'] = section_num

                text = ' '.join(contents)
                text = text.replace(' et al.', ' et al')     # escape 'et al.'
                doc = parse_sentences(nlp, text)

                i_base = 0
                for sen in doc.sents:
                    if len(sen) == 0:
                        continue
                    t_sentence = soup.new_tag('sentence')
                    raw_sen = str(sen.text)
                    raw_sen = raw_sen.replace(' et al', ' et al.')     # unescape 'et al.'
                    t_sentence['raw'] = raw_sen
                    for i, tok in enumerate(sen):
                        t_tok = soup.new_tag('token', idx=i)
                        form = tok.orth_
                        lemma = tok.lemma_
                        if i > 0 and sen[i-1].orth_ == 'et' and form == 'al':
                            # unescape 'et al.'
                            form = 'al.'
                            lemma = 'al.'
                        d = [
                            ('form', form),
                            ('lemma', lemma),
                            # POS
                            ('pos', tok.pos_),
                            ('tag', tok.tag_),
                            # dependency
                            ('head', (tok.head.i - i_base)),
                            ('dep', tok.dep_),
                            # named entity
                            ('ent_iob', tok.ent_iob_),
                            ('ent_type', tok.ent_type_),
                            # auxiliary info
                            ('is_stop', tok.is_stop),
                            ('is_oov', tok.is_oov),
                            ('prob', tok.prob),
                            ('cluster', tok.cluster),
                        ]
                        for k, v in d:
                            t = soup.new_tag(k)
                            t.string = str(v)
                            t_tok.append(t)
                        t_sentence.append(t_tok)

                    i_base += len(sen)
                    t_section.append(t_sentence)
                t_sections.append(t_section)
            t_paper.append(t_sections)

            # references
            t_references = soup.new_tag('references')
            for ref_authors, ref_title, ref_date, ref_booktitle in references:
                t_reference = soup.new_tag('reference')
                t_authors = soup.new_tag('authors')
                for author in authors:
                    t_author = soup.new_tag('author')
                    t_author.string = author
                    t_authors.append(t_author)
                t_reference.append(t_authors)
                t_ref_title = soup.new_tag('title')
                t_ref_title.string = ref_title
                t_reference.append(t_ref_title)
                t_ref_year = soup.new_tag('year')
                t_ref_year.string = ref_date
                t_reference.append(t_ref_year)
                t_ref_booktitle = soup.new_tag('booktitle')
                t_ref_booktitle.string = ref_booktitle
                t_reference.append(t_ref_booktitle)
                t_references.append(t_reference)
            t_paper.append(t_references)

            soup.append(t_paper)

            name, ext = os.path.splitext(path)
            out = name + '.spacy' + ext
            with open(out, 'w', encoding='utf-8') as f:
                print(str(soup), file=f)

        except Exception as e:
            print(str(e), file=sys.stderr)
            print('Failed to process: ' + path, file=sys.stderr)
            continue


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Extract document structure from Parscit files from ACL Anthology Reference Corpus.')
    parser.add_argument('data', nargs='+', help='XML files')

    main(parser.parse_args())
