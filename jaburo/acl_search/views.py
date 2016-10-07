from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import render

from . import es_api


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
