from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests

@csrf_exempt
def index(request):
    github_json = request.body.decode('utf-8')
    github_dict = json.loads(github_json)

    if github_dict['action'] == "assigned" and "issue" in github_dict.keys():
        print("Issue has been assigned")

        issue = github_dict['issue']

        new_branch_name = (str(issue['number']) + " " + issue['title']).lower().replace(' ', '-')
        print(new_branch_name)
        repo_url = issue['repository_url']

        r = requests.get(repo_url+"/branches")
        branch_names = [branch['name'] for branch in r.json()]

        print(new_branch_name in branch_names)

    else:
        print("Non-assign event")


    return HttpResponse("Done")
