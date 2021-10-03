# VBO Job Configuration Backup

## Install 

    pip install -r requirements.txt

## Overview

This repository is currently a proof-of-concept for the backup of the job configuration of a Veeam Office M365 instance.

The vbo_backup.py will save a job_data.json file which holds all the job configurations.

Inversely the vbo_restore.py will read the job_data.json and will provide two options:

1. Restore of Single Job
2. Restore all the Jobs

You will need to create a creds.json file for both backup and restore in the same folder as the python file.

    {
        "url": "192.168.1.1",
        "username": "administrator@admin.net",
        "password": "cGFzc3dvcmQ="
    }

Note that the password needs to be base64 encoded.

## How it works
### Backup

Note that all the API calls can be found here:

https://helpcenter.veeam.com/docs/vbo365/rest/overview.html?ver=50

First we get the organizations from:

    "https://{URL}:4443/v5/organizations"

To get the job configuration data we then need to run the following against each of the organization's ids:

    "https://{url}:4443/v5/organizations/{orgId}/Jobs"

This does not include the "selectedItems" that is required to restore jobs.

For that we need to get the URL from the "selectedItems" under "_links" key in the return object, then send another get request to it. That then needs to be added back to the original object. 

I noted that in testing that the key "title" was missing from the selectedItems nested object when it was a SharePoint site. In order to get around this I created a decorator that takes the result of the main run_get_jobs() function, and runs the check, adds the key if required and setting it to the 'name' value, which I found works.

Finally the data is saved to the job_data.json file.

### Restore

Below is a comparison of the data that is included in getting the jobs from the API vs what is required to create new jobs. 

| Item           | Get | Create | 
|----------------|-----| ------ |
| id             |  Y  |   N    |
| name           |  Y  |   Y    |
| description    |  Y  |   Y    |
| backupType     |  Y  |   Y    |
| schedulePolicy |  Y  |   Y    |
| proxyId        |  N  |   Y    |
| repositoryId   |  N  |   Y    |

You will notice that the proxyId and repositoryId keys are missing from the GET request.

I originally added these back to the object; however, I realized that if you are restoring after rebuilding VBO these IDs would be different. Therefore I decided to add a wizard that allows you to specify the Proxy and Repository for each job. 

The current version does not account for a change to the OrganizationId so I will likely need to add an additional step in the wizard.

The process that is taken is as follows:

1. Get the configured proxies
2. Get the configured repositories and add them to the proxy object
3. Provides a choice of restoring a job or all the jobs
4. For each job it will ask which proxy and repository needs to be used
5. Restores the job(s)

Step 3 loops through each of the jobs that are read from the jobs_data.json file. It then uses the select_proxy_repo function which provides the wizard and returns the proxy and repo ids that are then added to the object that needs to be sent to the API.

The all job restore version saves an updated file to "job_data_updated.json". The single restore version save it to "one_job_data.json"

## Easy Connect

This project uses a modified version of Veeam Easy Connect https://github.com/shapedthought/veeam-easy-connect which allows connection to VBO.

I will be updating that module with the VBO connection option soon.