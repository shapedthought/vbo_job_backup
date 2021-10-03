# job_backup.py

from veeam_easy_connect import VeeamEasyConnect
import requests
import json
import base64

def get_data(url: str, headers: dict) -> dict:
	""" Performs a GET request from the the API """
	res = requests.get(url, headers=headers, verify=False)
	res.raise_for_status()
	res_data = res.json()
	return res_data

def check_sharepoint(data: list[dict]) -> list[dict]:
	""" Checks the item is a SharePoint site and 
		if it is missing the "title" item and replaces
		it if it is.
	 """
	for i in data:
		if len(i['jobData']) > 0:
			for j in i['jobData']:
				for k in j['selectedItems']:
					if k['type'] == "Site" and "title" not in k['site']:
						k['site']['title'] = k['site']['name']
	return data

def check_sharepoint_dec(func):
	""" 
		Checks the if the item is a SharePoint site and 
		if it is missing the "title" item and replaces it with
		the site name which appears to be the same most of the time.
		Turned this into a decorator because why not?
	 """
	def wrapper(*args, **kwargs):
		data = func(*args, **kwargs)
		for i in data:
			if len(i['jobData']) > 0:
				for j in i['jobData']:
					for k in j['selectedItems']:
						if k['type'] == "Site" and "title" not in k['site']:
							k['site']['title'] = k['site']['name']
		return data
	return wrapper

@check_sharepoint_dec
def run_get_jobs(org_data: list[dict], url: str, headers: dict) -> list[dict]:
	"""
		Gets the jobs by org, then gets the selected items from each job and
		adds them to the job object. 
		It then returns a new object with the Organization (currently named jobName)
		id, and the associated jobs in a list.
	"""
	jobs_org = []
	for i in org_data:
		org_url = f"https://{url}:4443/v5/organizations/{i['id']}/Jobs"
		job_data = get_data(org_url, headers)
		# job through each of the job instances
		for j in job_data:
		# If the backupType is selectedItems
			if j['backupType'] == "SelectedItems":
				# get the selected items URL
				select_url = j['_links']['selectedItems']['href']
				# get the data
				select_data = get_data(select_url, headers)
				# add the selected items to the job data object
				j['selectedItems'] = select_data
				job_dict = {
				"jobName": i['name'], # actually org name
				"id": i['id'], # org id
				"jobData": job_data
				}
				jobs_org.append(job_dict)
	return jobs_org


def main() -> None:
	with open("creds.json", "r") as creds_file:
		creds = json.load(creds_file)

	base64_bytes = creds['password'].encode("ascii")
	pass_string_bytes = base64.b64decode(base64_bytes)
	PASSWORD = pass_string_bytes.decode("ascii")

	URL = creds['url']
	USERNAME = creds['username']
	# PASSWORD = "2Ch1mps4"

	vec = VeeamEasyConnect()

	headers = vec.vbo_login_base(URL, USERNAME, PASSWORD)
	
	org_url = f"https://{URL}:4443/v5/organizations"

	org_data = get_data(org_url, headers)

	jobs_org = run_get_jobs(org_data, URL, headers)

	# job_dict_check = check_sharepoint(jobs_org)

	with open("job_data.json", "w") as json_file:
		json.dump(jobs_org, json_file, indent=2)

	print("Done")



if __name__ == "__main__":
	main()