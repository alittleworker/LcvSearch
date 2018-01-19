import json
from django.shortcuts import render
from django.views.generic.base import View
from search.models import ArticleType
from django.http import HttpResponse
from datetime import datetime
from elasticsearch import Elasticsearch

client = Elasticsearch(hosts=["127.0.0.1", "192.168.1.99"])

# Create your views here.
class IndexView(View):
    #首页
    def get(self, request):
        return render(request, "index.html" )


class SearchSuggest(View):
    def get(self, request):
        key_words = request.GET.get('s','')
        re_datas = []
        if key_words:
            s = ArticleType.search()
            s = s.suggest('my_suggest', key_words, completion={
                "field":"suggest",
                "fuzzy":{
                    "fuzziness":2
                },
                "size":10
            })
            suggestions = s.execute().suggest
            for match in suggestions.my_suggest[0].options:
                source = match._source
                re_datas.append(source["title"])

            return HttpResponse(json.dumps(re_datas), content_type="application/json")


class SearchView(View):
    def get(self, request):
        key_words = request.GET.get("q","")
        response = client.search(
            index="jobbole",
            body={
                "query":{
                    "multi_match":{
                        "query":key_words,
                        "fields":["tags", "title", "content"]
                    }
                },
                "from":0,
                "size":4,
                "highlight":{
                    "pre_tags":['<span class="keyWord">'],
                    "post_tags":['</span>'],
                    "fields":{
                        "title":{},
                        "content":{}
                    }
                }
            }
        )

        total_nums = response["hits"]["total"]
        hit_list = []
        for hit in response["hits"]["hits"]:
            hit_dict = {}
            if "title" in hit["highlight"]:
                hit_dict["title"] = "".join(hit["highlight"]["title"])
            else:
                hit_dict["title"] = "".join(hit["_source"]["title"][0])

            if "content" in hit["highlight"]:
                hit_dict["content"] = "".join(hit["highlight"]["content"])[:500]
            else:
                hit_dict["content"] = "".join(hit["_source"]["content"])[:500]

            hit_dict["create_date"] = hit["_source"]["creat_date"]
            hit_dict["url"] = hit["_source"]["url"]
            hit_dict["score"] = hit["_score"]

            hit_list.append(hit_dict)

        return render(request, "result.html", {"all_hits":hit_list, "key_words": key_words})




