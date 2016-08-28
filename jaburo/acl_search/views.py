from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import render

from . import es_api
from .analysis import analyze_text, generate_text


DEFAULT_PHRASE_NUM = 30
DEFAULT_EXAMPLE_NUM = 10


def search(request):
    return render(request, 'acl_search/search.html', {
        'search_phrases_url': reverse('search_phrases'),
        'search_examples_url': reverse('search_examples'),
        'init_query': request.GET.get('query', ''),
        'init_mode': request.GET.get('mode', ''),
        'init_like': request.GET.get('like'),
    })


def lm(request):
    return render(request, 'acl_search/lm.html')


def search_phrases(request):
    query = request.GET.get('q', '')
    size = request.GET.get('size', DEFAULT_PHRASE_NUM)
    slop = request.GET.get('slop', 3)
    like_str = request.GET.get('like')
    like = (like_str != 'false' and like_str)
    only_verb_phrase = request.GET.get('verb', False)

    # TODO: sanitize input

    phrases = es_api.search_phrases(query, size,
                                    highlight=True,
                                    only_verb_phrase=only_verb_phrase,
                                    slop=slop,
                                    like=like,
                                    )
    res = {
        'hits': phrases
    }
    return JsonResponse(res)


def search_examples(request):
    query = request.GET.get('q', '')
    size = request.GET.get('size', DEFAULT_EXAMPLE_NUM)
    prefix = request.GET.get('prefix', False)
    slop = request.GET.get('slop', 0)
    sections = request.GET.get('sections', '')
    like_str = request.GET.get('like')
    like = (like_str != 'false' and like_str)

    # TODO: sanitize input

    total_hits, papers = es_api.search_examples(query, size, sections=sections, highlight=True, prefix=prefix, slop=slop, like=like)
    res = {
        'total': total_hits,
        'hits': papers,
    }
    return JsonResponse(res)


def analyze(request):
    section = request.GET.get('section', '')
    text = request.GET.get('text', '')
    res = analyze_text(section, text)
    #import json
    #print(json.dumps(res['text'], indent=2))
    return JsonResponse(res)


def generate(request):
    section = request.GET.get('section', '')
    text = request.GET.get('text', '')
    temp = float(request.GET.get('temp', '3.0'))
    random = bool(request.GET.get('temp', 'True'))
    max_len = int(request.GET.get('max_len', 300))
    res = generate_text(section, text, temp, random, max_len)
    return JsonResponse(res)
