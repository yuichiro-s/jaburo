from django.conf import settings
from collections import defaultdict

from .models import Paper


PHRASE_INDEX = 'phrase'
PHRASE_TYPE = 'phrase'
SENTENCE_INDEX = 'sentence'
SENTENCE_TYPE = 'sentence'

UNLIMITED = 10000


def search_phrases(query, size, highlight=True, only_verb_phrase=False, slop=0, like=False):

    colors = defaultdict(lambda: 'rgb(255,255,255)')
    colors['V'] = 'rgb(255, 200, 200)'
    colors['J'] = 'rgb(200, 255, 200)'
    colors['N'] = 'rgb(200, 200, 255)'
    colors['P'] = 'rgb(200, 200, 255)'

    freq_sort = not like

    if like:
        q = {
            'more_like_this': {
                'fields': ['phrase'],
                'like': query,
                "min_term_freq": 1,
                "max_query_terms": 12,
            },
        }
    else:
        q = {
            'match_phrase_prefix': {
                'phrase': {
                    'query': query,
                    'slop': slop,
                    'max_expansions': 50,
                }
            },
        }

    obj = {
        'query': {
            'bool': {
                'must': [
                    q,
                    {'match_phrase_prefix': {'tags': 'V'}} if only_verb_phrase else {}
                ]
            }
        },
        'sort': [
            {'freq': 'desc'} if freq_sort else {},
            '_score',
        ],
        'highlight': {
            'fields': ({'phrase': {'number_of_fragments': 0}} if highlight else {})
        },
        'size': size,
    }

    results = settings.ES_CLIENT.search(
        index=PHRASE_INDEX,
        doc_type=PHRASE_TYPE,
        body=obj
    )

    phrases = []
    for d in results['hits']['hits']:

        score = d['_score']
        source = d['_source']
        if 'highlight' in d:
            phrase = d['highlight']['phrase'][0]
        else:
            phrase = source['phrase']
        freq = source['freq']
        tags = source['tags']

        toks = phrase.split()
        assert len(toks) == len(tags)
        new_phrase = ''
        for i, (tok, tag) in enumerate(zip(toks, tags)):
            color = colors[tag]
            new_tok = '<span style="background-color: {}">{}</span>'.format(color, tok)
            #if tok != '-' and (i == len(toks)-1 or toks[i+1] != '-'):
            #    new_tok += ' '
            new_tok += ' '
            new_phrase += new_tok

        if 'be' not in phrase.split():
            phrases.append({
                'score': score,
                #'phrase': phrase,
                'phrase': new_phrase,
                'freq': freq,
                'tags': tags,
            })

    return phrases


def search_examples(query, size, sections='', highlight=True, prefix=False, slop=0, like=False):

    freq_sort = not like

    if like:
        q = {
            'more_like_this': {
                'fields': ['body'],
                'like': query,
                "min_term_freq": 1,
                "max_query_terms": 12,
            },
        }
    else:
        q = {
            ('match_phrase_prefix' if prefix else 'match_phrase'): {
                'body': {
                    'query': query,
                    'slop': slop,
                    'max_expansions': 50,
                }
            },
        }

    obj = {
        'query': {
            'bool': {
                'must': [
                    q,
                    {'match': {'section': sections}} if sections else {},   # filter with sections
                ]

            }
        },
        'aggs': {
            'papers': {
                'terms': {
                    'field': 'paper',
                    'size': size,
                },
                'aggs': {
                    'sections': {
                        'terms': {
                            'field': 'section_offset',
                            'order': {
                                '_term': 'asc'
                            }
                        }
                    }
                }
            }
        }
    }

    results = settings.ES_CLIENT.search(
        index=SENTENCE_INDEX,
        doc_type=SENTENCE_TYPE,
        body=obj
    )

    total_hits = results['hits']['total']
    paper_ids = list(map(lambda d: d['key'], results['aggregations']['papers']['buckets']))

    obj_lst = []
    header = {
        'index': SENTENCE_INDEX,
        'type': SENTENCE_TYPE,
    }

    paper_objs = []

    if freq_sort:
        for paper_id in paper_ids:
            body = {
                'query': {
                    'bool': {
                        'must': [
                            {'match': {'paper': paper_id}},
                            {'match': {'section': sections}} if sections else {},   # filter with sections
                            q,
                            #{('match_phrase_prefix' if prefix else 'match_phrase'): {
                            #    'body': {
                            #        'query': query,
                            #        'slop': slop,
                            #        'max_expansions': 50,
                            #    }
                            #}},
                        ]
                    }
                },
                'highlight': {
                    'fields': ({'body': {'number_of_fragments': 0}} if highlight else {})
                },
                'size': UNLIMITED,
            }
            obj_lst.append(header)
            obj_lst.append(body)

        if len(paper_ids) == 0:
            responses = []
        else:
            responses = settings.ES_CLIENT.msearch(body=obj_lst)['responses']
        assert len(responses) == len(paper_ids)
        for paper_id, res in zip(paper_ids, responses):
            paper_obj = f(paper_id, res['hits']['hits'])
            paper_objs.append(paper_obj)

    else:
        hits = results['hits']['hits']
        for h in hits:
            paper_id = h['_source']['paper']
            paper_obj = f(paper_id, [h])
            paper_objs.append(paper_obj)

    return total_hits, paper_objs


def f(paper_id, hits):
    sections = defaultdict(list)
    for d in hits:
        source = d['_source']
        if 'highlight' in d:
            sen = d['highlight']['body'][0]
        else:
            sen = source['body']
        offset = source['offset']
        section = source['section']
        section_num = source['section_num']
        section_offset = source['section_offset']
        sections[(section_offset, section_num, section)].append((offset, sen))

    sec_objs = []
    count = 0
    for (_, section_num, section), sens in sorted(sections.items()):
        sorted_sens = list(map(lambda n_sen: n_sen[1], sorted(sens)))
        sec_objs.append({
            'num': section_num,
            'section': section,
            'sens': sorted_sens,
        })
        count += len(sens)

    try:
        paper = Paper.objects.get(paper_id=paper_id.replace('_', '-'))
        title = paper.title
        authors = paper.authors.split('+')
        year = paper.year
        conference = paper.conference
        url = paper.url
    except Paper.DoesNotExist:
        title = ''
        authors = []
        year = 0
        conference = ''
        url = ''
    paper_obj = {
        'id': paper_id,
        'sections': sec_objs,
        'count': count,
        'title': title,
        'authors': authors,
        'year': year,
        'conference': conference,
        'url': url,
    }
    return paper_obj
