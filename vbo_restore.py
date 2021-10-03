#  vbo_restore.py

from veeam_easy_connect import VeeamEasyConnect
import requests
import json
from rich.prompt import Prompt
import pprint
import logging
from typing import Tuple
import sys
from rich.table import Table
from rich.console import Console
import PySimpleGUI as sg

# logging.basicConfig(filename='job_creation.log', encoding='utf-8', level=logging.DEBUG)
logging.basicConfig(filename='app.log', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

URL = "192.168.3.7"
USERNAME = "administrator@testlab.net"
PASSWORD = "2Ch1mps4"
    
vec = VeeamEasyConnect()
console = Console()
headers = vec.vbo_login_base(URL, USERNAME, PASSWORD)


# Get method
def get_data(url: str, headers: dict) -> dict:
    res = requests.get(url, headers=headers, verify=False)
    res.raise_for_status()
    res_data = res.json()
    return res_data


# Post method
def post_data(url: str, headers: dict, data: dict) -> dict:
    res = requests.post(url, headers=headers, data=data, verify=False)
    res.raise_for_status()
    res_data = res.json()
    return res_data


def save_json(name: str, data: list[dict]) -> None:
    with open(name, "w") as json_file:
        json.dump(data, json_file, indent=2)


repo_proxy_map = []
proxy_names = []

# get the proxy data
proxy_url = f"https://{URL}:4443/v5/Proxies?extendedView=true"
proxy_data = get_data(proxy_url, headers)


# get and map the repos to the proxies
for i in proxy_data:
    all_repo_data = []
    repo_urls = i['_links']['repositories']['href']
    repo_res = get_data(repo_urls, headers)
    i['repoInfo'] = repo_res
    repo_proxy_map.append(i)


# create list of the names
proxy_names = [x['description'] for x in repo_proxy_map]


def select_proxy_repo() -> Tuple[str, str]:
    proxy_table = Table(title="Proxies")
    proxy_table.add_column("Index", justify="center", style="cyan")
    proxy_table.add_column("Name", justify="center", style="cyan")
    for index, item in enumerate(proxy_names):
        proxy_table.add_row(str(index), item)
        # print(f"{index} - {item}")
    console.print(proxy_table)

    selected_proxy = Prompt.ask("Enter the select the proxy index")

    repo_table = Table(title="Repositories")
    repo_table.add_column("Index", justify="center", style="cyan")
    repo_table.add_column("Name", justify="center", style="cyan")
    for i in repo_proxy_map:
        if i['description'] == proxy_names[int(selected_proxy)]:
            # saving the selected proxy object
            proxy_data = i
            proxy_id = i['id']
            for index, j in enumerate(i['repoInfo']):
                repo_table.add_row(str(index), j['name'])
                # print(f"{index} - {j['name']}")
    console.print(repo_table)

    index = Prompt.ask("Select the repo index required for the job")

    repo_id = proxy_data['repoInfo'][int(index)]['id']

    # returns the proxy and repo for that job that can be added to the object
    return proxy_id, repo_id


def restore_job(data: dict) -> None:
    post_data(data, headers, data)


def create_job(id: str, headers: dict, data: dict) -> None:
    try:
        post_url = f"https://{URL}:4443/v5/Organizations/{id}/Jobs"
        pprint.pprint(data)
        job_res = post_data(post_url, headers, json.dumps(data))
        print("Success!")
    except Exception as e:
        print(e)
        logging.error("Exception occurred", exc_info=True)

with open("job_data_old.json", "r") as job_file:
    job_data = json.load(job_file)


print("This wizard can restore one or all of your VBO jobs.")

res = Prompt.ask("Select a single job to restore?", choices=["Y", "N"])

if res == "Y":

    job_data_filt = []
    job_data_flat = []
    for i in job_data:
        if len(i['jobData']) > 0:
            job_data_filt.append(i)
            for j in i['jobData']:
                job_data_flat.append({
                    "org": i['jobName'],
                    "jobName": j['name'],
                    "description": j['description']})

    table = Table(title="Jobs Found")
    table.add_column("Index", justify="center", style="cyan")
    table.add_column("Org", justify="center", style="cyan")
    table.add_column("Job Name", justify="center", style="cyan")
    table.add_column("Description", justify="center", style="cyan")

    for index, i in enumerate(job_data_flat):
        table.add_row(str(index), i['org'], i['jobName'], i['description'])
        # print(f"{index} - Org: {i['org']} - Job Name: {i['jobName']} - Description: {i['description']}")
    # console = Console()
    console.print(table)
    choices = list(range(0, len(job_data_flat)))
    c_int = list(map(str, choices))
    job_index = Prompt.ask("Select a job index to restore", choices=c_int)


    selected_job = job_data_flat[int(job_index)]
    for i in job_data_filt:
        if i['jobName'] == selected_job['org']:
            for j in i['jobData']:
                if j['name'] == selected_job['jobName']:
                    proxy_id, repo_id = select_proxy_repo()
                    j['proxyId'] = proxy_id
                    j['repositoryId'] = repo_id
                    del j['lastRun']
                    del j['nextRun']
                    del j['_links']
                    del j['id']
                    save_json("one_job_data.json", j)
                    res = Prompt.ask("Restore the job?", choices=["Y", "N"])
                    if res == "Y":
                        create_job(i['id'], headers, j)
                    else:
                        print("Job has not been created, exiting")
                        sys.exit()
                        

if res == "N":
    print("This wizard will take you through each of the jobs where you can select the current proxies and repos")
    for index, i in  enumerate(job_data):
        if len(i['jobData']) > 0:
            for j in i['jobData']:
                print(f"Job Name: {j['name']}, Description: {j['description']}")
                proxy_id, repo_id = select_proxy_repo()
                j['proxyId'] = proxy_id
                j['repositoryId'] = repo_id
    save_json("job_data_updated.json", i)
    res_job = Prompt.ask("Are you happy to proceed with restoring all jobs?")
    if res_job == "Y":
        for i in job_data:
            for j in i['jobData']:
                if len(i['jobData']) > 0:
                    del j['lastRun']
                    del j['nextRun']
                    del j['_links']
                    del j['id']
                    create_job(i['id'], headers, j)
    else:
        print("Jobs have not been created, exiting")
        sys.exit()
