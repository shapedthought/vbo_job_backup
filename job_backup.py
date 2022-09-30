# job_backup.py

from veeam_easy_connect import VeeamEasyConnect
import requests
import json
import base64
from halo import Halo

spinner = Halo(text='Loading', spinner='dots')


def get_data(url: str, headers: dict) -> dict:
    """ Performs a GET request from the the API """
    res = requests.get(url, headers=headers, verify=False)

    res.raise_for_status()
    res_data = res.json()

    return res_data


def run_get_jobs(org_data: list[dict], vec: VeeamEasyConnect) -> list[dict]:
    """
            Gets the jobs by org, then gets the selected items from each job and
            adds them to the job object. 
            It then returns a new object with the Organization (currently named jobName)
            id, and the associated jobs in a list.
    """
    jobs_org = []
    spinner.start()
    for i in org_data:
        org_url = f"organizations/{i['id']}/Jobs"
        job_data = vec.get(org_url, False)

        # job through each of the job instances
        for j in job_data:
            # If the backupType is selectedItems
            if j['backupType'] == "SelectedItems":
                # get the selected items URL
                select_url = j['_links']['selectedItems']['href']
                # get the data
                select_data = vec.get(select_url[3:], False)
                # add the selected items to the job data object
                j['selectedItems'] = select_data

        job_dict = {
            "jobName": i['name'],  # actually org name
            "id": i['id'],  # org id
            "jobData": job_data
        }
        jobs_org.append(job_dict)
    spinner.stop()
    return jobs_org


def main() -> None:
    with open("creds.json", "r") as creds_file:
        creds = json.load(creds_file)

    base64_bytes = creds['password'].encode("ascii")
    pass_string_bytes = base64.b64decode(base64_bytes)
    PASSWORD = pass_string_bytes.decode("ascii")

    URL = creds['url']
    USERNAME = creds['username']

    vec = VeeamEasyConnect(USERNAME, PASSWORD, False)

    vec.o365().login(URL)

    org_data = vec.get("organizations", False)

    jobs_org = run_get_jobs(org_data, vec)

    # job_dict_check = check_sharepoint(jobs_org)

    with open("job_data.json", "w") as json_file:
        json.dump(jobs_org, json_file, indent=2)

    print("Done")


if __name__ == "__main__":
    main()
