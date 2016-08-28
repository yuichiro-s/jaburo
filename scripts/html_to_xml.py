import re
import bs4
import spacy


def parse_html(path):
    with open(path) as f:
        soup = bs4.BeautifulSoup(f, 'html.parser')

        abstract = None
        sections = []
        current_section = None
        current_depth = None
        current_paragraphs = None

        # find abstract
        state = 0   # 0: before abstract
        for p in soup.find('html').descendants:
            if state == 0:
                if p.name == 'p' and p.has_attr('class') and 'abstract' in p['class']:
                    abstract = p.string
                    state = 1
            else:
                if type(p) == bs4.element.Tag:
                    if p.name.startswith('h'):
                        depth = int(p.name[1:])
                        # section start
                        if current_section is not None:
                            sections.append((current_section, current_depth, current_paragraphs))
                        current_section = p.string
                        current_depth = depth
                        current_paragraphs = []
                    elif p.name == 'p':
                        # paragraph
                        current_paragraphs.append(p.string)
        if current_section is not None:
            sections.append((current_section, current_depth, current_paragraphs))

    return abstract, sections


def clean_paragraphs(paragraphs):
    # detect non-terminated paragraph fragments
    # remove tables, figures, and page numbers
    # TODO
    cleaned_paragraphs = []

    """
    ignore = False
    for p in paragraphs:
        if not ignore and not p.endswith('.'):
            #



        p

    pass
    """
    return paragraphs


def extract_sentences(nlp, paragraph):
    #return list(map(lambda s: s.text, nlp(paragraph).sents))
    return paragraph.split('.')


def fix_ocr_errors(sentence):
    # try to fix OCR errors
    # separate concatenated words
    # TODO
    return sentence


def main(args):
    #nlp = spacy.load('en')
    nlp = None

    for path in args.data:
        abstract, sections = parse_html(path)

        #soup = bs4.BeautifulSoup(features='xml')
        #soup = bs4.BeautifulSoup('html.parser')
        soup = bs4.BeautifulSoup()

        t_paper = soup.new_tag('paper')
        t_abstract = soup.new_tag('abstract')
        t_abstract.string = abstract
        t_paper.append(t_abstract)

        # merge paragraphs and split into sentences
        last_depth = 0
        tag_stack = [t_paper]
        for title, depth, paragraphs in sections:
            t_section = soup.new_tag('section', title=title)

            # clean up paragraphs
            cleaned_paragraphs = clean_paragraphs(paragraphs)
            for paragraph in cleaned_paragraphs:
                sentences = extract_sentences(nlp, paragraph)
                fixed_sentences = map(fix_ocr_errors, sentences)
                for sen in fixed_sentences:
                    t_sentence = soup.new_tag('sentence')
                    t_sentence.string = sen
                    t_section.append(t_sentence)

            # construct section hierarchy
            if depth <= last_depth:
                tag_stack.pop()
            tag_stack[-1].append(t_section)
            tag_stack.append(t_section)
            last_depth = depth

        soup.append(t_paper)

        print(str(soup))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Extract document structure from HTML files created by Abekawa-san\'s tool.')
    parser.add_argument('data', nargs='+', help='HTML files')

    main(parser.parse_args())
