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

def run_get_jobs(org_data: list[dict], url: str, headers: dict) -> list[dict]:
	"""
		Gets the jobs by org, then gets the selected items from each job and
		adds them to the job object. 
		It then returns a new object with the Organization (currently named jobName)
		id, and the associated jobs in a list.
	"""
	jobs_org = []
	
	for i in org_data:
		# sp_url = f"https://192.168.3.7:4443/v5/Organizations/{i['id']}/Sites?includePersonalSites=true"
		# sp_data = get_data(sp_url, headers)
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
		backup_types = []
		for k in job_data:
			if "selectedItems" in k:
				for j in k['selectedItems']:
					backup_types.append(j['type'])
		if "Site" in backup_types:
			print("SharePoint backups found, getting config, this might take a moment")
			# https://helpcenter.veeam.com/docs/vbo365/rest/get_organizations_id_sites_siteid.html?zoom_highlight=title&ver=50
			# https://192.168.3.7:4443/v5/Organizations/6d5a58d2-aea3-4eb9-b8cc-c707bbf75d57/Sites/fb3c7d7b-09c9-4b35-b50a-cf586ae6fac2fde71eaf-4469-4ac4-b616-761b9420549e
			# The above is much faster than the current one
			# to use the new end point I will need to get the site ID for each sharepoint instance. 
			spinner.start()
			for i in job_data:
				if 'selectedItems' in i:
					if len(i['selectedItems']) > 0:
						for e in i['selectedItems']:
							if e['type'] == "Site":
								sp_job_url = f"https://{url}:4443/v5/Organizations/6d5a58d2-aea3-4eb9-b8cc-c707bbf75d57/Sites/{e['site']['id']}"
								sp_job_data = get_data(sp_job_url, headers)
								e['site']['isCloud'] = sp_job_data['isCloud']
								e['site']['isPersonal'] = sp_job_data['isPersonal']
								e['site']['isAvailable']= sp_job_data['isAvailable']
								e['site']['title'] = sp_job_data['title']
			spinner.stop()
			
			# sp_url = f"https://{url}:4443/v5/Organizations/{i['id']}/Sites?includePersonalSites=true"
			# sp_data = get_data(sp_url, headers)

			# for c in sp_data['results']:
			# 	for d in job_data:
			# 		if len(d['selectedItems']) > 0 :
			# 			for e in d['selectedItems']:
			# 				try:
			# 					if e['site']['name'] == c['name'] and e['type'] == 'Site':
			# 						e['site']['isCloud'] = c['isCloud']
			# 						e['site']['isPersonal'] = c['isPersonal']
			# 						e['site']['isAvailable']= c['isAvailable']
			# 						e['site']['title'] = c['title']
			# 				except:
			# 					pass
		
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