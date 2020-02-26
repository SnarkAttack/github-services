from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import os

@csrf_exempt
def index(request):
    headers = {"Accept": "application/vnd.github.inertia-preview+json", 
                       'Authorization': 'token %s' % os.getenv("GITHUB_PAT", "None")}
    
    github_json = request.body.decode('utf-8')
    github_dict = json.loads(github_json)

    if github_dict.get('action', None) == "assigned" and "issue" in github_dict.keys():
        print("Assign event")
        
        issue = github_dict['issue']

        new_branch_name = (str(issue['number']) + " " + issue['title']).lower().replace(' ', '-')
        repo_url = issue['repository_url']

        r = requests.get(repo_url+"/branches", headers = headers)
        branches = r.json()
        branch_names = [branch['name'] for branch in branches]
        
        t = requests.get(repo_url+"/projects", headers=headers)

        # Needs to not just be 0
        q = requests.get(t.json()[0]['columns_url'], headers=headers)
        
        todo_cards_url = None
        in_progress_col_id = None
        
        for column in q.json():
            if column['name'].lower() == "to do" or column['name'].lower() == 'todo':
                todo_cards_url = column['cards_url']
            elif column['name'].lower() == 'in progress':
                in_progress_col_id = column['id']
                
        if todo_cards_url is not None:
            y = requests.get(todo_cards_url, headers=headers)
            for card in y.json():
                z = requests.get(card['content_url'], headers=headers)
                
                if z.json()['title'] == issue['title']:
                    
                    move_resp = requests.post(card['url']+"/moves", headers=headers, 
                                              data = json.dumps({"position": "top", "column_id": in_progress_col_id}))
        

        if new_branch_name not in branch_names:
            n = requests.get(repo_url, headers=headers)
            default_branch = n.json()['default_branch']
            default_branch_sha = [d for d in branches if d['name'] == default_branch][0]['commit']['sha']
            
            x = requests.post(repo_url + "/git/refs", 
                headers = headers,
                data = json.dumps({ "ref": "refs/heads/"+new_branch_name, "sha": default_branch_sha }))

    elif github_dict.get('action', None) == "unassigned" and "issue" in github_dict.keys():
        print("Unassign event")
        
        issue = github_dict['issue']
        repo_url = issue['repository_url']
        
        # No one has this ticket assigned, move it back to To do
        if len(issue['assignees']) == 0:
            t = requests.get(repo_url+"/projects", headers=headers)

            # Needs to not just be 0
            q = requests.get(t.json()[0]['columns_url'], headers=headers)
            
            in_progress_url = None
            todo_col_id = None
            
            for column in q.json():
                if column['name'].lower() == "to do" or column['name'].lower() == 'todo':
                    todo_col_id = column['id']
                elif column['name'].lower() == 'in progress':
                    in_progress_url = column['cards_url']
                    
            if in_progress_url is not None:
                y = requests.get(in_progress_url, headers=headers)
                for card in y.json():
                    z = requests.get(card['content_url'], headers=headers)
                    
                    if z.json()['title'] == issue['title']:
                        
                        move_resp = requests.post(card['url']+"/moves", headers=headers, 
                                                data = json.dumps({"position": "top", "column_id": todo_col_id}))

    else:
        print("Non-assign event")

    return HttpResponse("Done")
