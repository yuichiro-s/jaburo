from django.conf import settings
from collections import defaultdict


from .rnnlm import score, generate

import numpy as np


def calc_color(tok, prob, alternative_list):
    w, p = tok
    w = w.lower()
    ws = map(lambda w_p: w_p['w'], alternative_list)
    #color = 'rgb(0, 0, 0)'
    color = None
    if w not in ws:
        top_idx = 1 if alternative_list[0] == '<UNK>' else 0
        top_prob = alternative_list[top_idx]['p']
        if top_prob > 0.5:
            color = 'rgb(255, 200, 200)'
        elif (p.startswith('P') or p.startswith('D')) and top_prob / prob > 3:
            color = 'rgb(255, 200, 200)'
        #elif top_prob / prob > 1000:
        #    color = 'rgb(255, 200, 200)'
    return color


def analyze_text(section, text):
    # tokenize
    section_doc = settings.SPACY_EN_MODEL(section)
    text_doc = settings.SPACY_EN_MODEL(text)
    section_toks = list(map(lambda t: (t.text, t.tag_), section_doc))
    text_toks = list(map(lambda t: (t.text, t.tag_), text_doc))
    #section_doc = section.split()
    #text_doc = text.split()
    #section_toks = list(map(lambda t: (t, t), section_doc))
    #text_toks = list(map(lambda t: (t, t), text_doc))

    # run LM
    lm_input = ['__t__'] + list(map(lambda t: t[0].lower(), section_toks)) + ['__s__'] + list(map(lambda t: t[0].lower(), text_toks))
    lm_results = score(lm_input)

    assert len(lm_results) == len(section_toks) + len(text_toks) + 1

    lm_results = list(map(lambda t: {
        'prob': t[0],
        'top': list(map(lambda w_p: {'w': w_p[0], 'p': w_p[1]}, t[1])),
    }, lm_results))

    def process_tok(tok):
        return {
            'tok': tok[0][0],
            'tag': tok[0][1],
            'lm': tok[1],
            'color': calc_color(tok[0], tok[1]['prob'], tok[1]['top']),
        }

    section_obj = list(map(process_tok, zip(section_toks, lm_results[0:len(section_toks)])))
    text_obj = list(map(process_tok, zip(text_toks, lm_results[1+len(section_toks):])))

    sens_obj = []
    i = 0
    for sent in text_doc.sents:
        sen_obj = []
        for _ in sent:
            sen_obj.append(text_obj[i])
            i += 1
        sens_obj.append(sen_obj)
    #sen_obj = []
    #print(text_obj)
    #for obj in text_obj:
    #    sen_obj.append(obj)
    #    print(obj)
    #    if obj['tok'].endswith('.'):
    #        sens_obj.append(sen_obj)
    #        sen_obj = []
    #if sen_obj:
    #    sens_obj.append(sen_obj)

    obj = {
        'section': section_obj,
        'text': sens_obj,
    }

    return obj


def generate_text(section, text, temp, random, max_len):
    #section_doc = settings.SPACY_EN_MODEL(section)
    #text_doc = settings.SPACY_EN_MODEL(text)
    #section_toks = list(map(lambda t: (t.text, t.tag_), section_doc))
    #text_toks = list(map(lambda t: (t.text, t.tag_), text_doc))
    section_doc = section.split()
    text_doc = text.split()
    section_toks = list(map(lambda t: (t, t), section_doc))
    text_toks = list(map(lambda t: (t, t), text_doc))

    # run LM
    lm_input = ['__t__'] + list(map(lambda t: t[0].lower(), section_toks)) + ['__s__'] + list(map(lambda t: t[0].lower(), text_toks))
    lm_results = generate(lm_input, temp=temp, random=random, max_len=max_len)
    obj = {
        'text': lm_results,
    }

    return obj
