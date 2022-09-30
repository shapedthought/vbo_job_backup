# V365 Job Configuration Backup

## Updates

- This has been updated to VB365 v6, and now uses the Veeam Easy Connect module.
- VB365 v6 had some API improvements which has simplified the process and script, so should run faster.
- Backup files will be saved with the date and time of backup.
- On restores if there are more than one json file in the directory, it will ask you to select one of them to use.
- If a "creds.json" file is not present, both backup and restore can take you through a wizard to create one.

## Install

    pip install -r requirements.txt

## Overview

This repository is currently a proof-of-concept for the backup of the job configuration of a Veeam Office M365 instance.

The vbo_backup.py will save a job_data-DATETIME.json file which holds all the job configurations.

Inversely the vbo_restore.py will read the job_data.json and will provide two options:

1. Restore of Single Job
2. Restore all the Jobs

A creds.json file is required for both backup and restore in the same folder as the python file.

If one doesn't exist in the folder, the script can take you through the process of creating one.

    {
        "url": "192.168.1.1",
        "username": "administrator@admin.net",
        "password": "cGFzc3dvcmQ="
    }

Note that the passwords are based64 encoded.

## How it works

### Backup

Note that all the API calls can be found here:

https://helpcenter.veeam.com/docs/vbo365/rest/overview.html?ver=60

First we get the organizations from:

    "https://{URL}:4443/v6/organizations"

To get the job configuration data we then need to run the following against each of the organization's ids:

    "https://{url}:4443/v6/organizations/{orgId}/Jobs"

This does not include the "selectedItems" that is required to restore jobs.

For that we need to get the URL from the "selectedItems" under "\_links" key in the return object, then send another get request to it. That then needs to be added back to the original object.

    f"https://{url}:4443/v6/Organizations/6d5a58d2-aea3-4eb9-b8cc-c707bbf75d57/Sites/{siteId}"

Finally the data is saved to the job_data-DATETIME.json file.

### Restore

Below is a comparison of the data that is included in getting the jobs from the API vs what is required to create new jobs.

| Item           | Get | Create |
| -------------- | --- | ------ |
| id             | Y   | N      |
| name           | Y   | Y      |
| description    | Y   | Y      |
| backupType     | Y   | Y      |
| schedulePolicy | Y   | Y      |
| proxyId        | N   | Y      |
| repositoryId   | N   | Y      |

You will notice that the proxyId and repositoryId keys are missing from the GET request.

I originally added these back to the object; however, I realized that if you are restoring after rebuilding VB365 these IDs would be different. Therefore I decided to add a wizard that allows you to specify the Proxy and Repository in the current VB365 instance.

The current version does not account for a change to the OrganizationId so I will likely need to add an additional step in the wizard.

The process that is taken is as follows:

1. Get the configured proxies
2. Get the configured repositories and add them to the proxy object
3. Checks the folder for .json files and if there is more than one, it will prompt for a selection
4. Provides a choice of restoring a job or all the jobs
5. For each job it will ask which proxy and repository needs to be used
6. Restores the job(s)

Step 3 loops through each of the jobs that are read from the jobs_data.json file. It then uses the select_proxy_repo function which provides the wizard and returns the proxy and repo ids that are then added to the object that needs to be sent to the API.

The all job restore version saves an updated file to "job_data_updated.json". The single restore is saved to "one_job_data.json"

## Notes on restore points

After performing a new backup after restore you will find that only the backups from that new job will be shown at the job level.

To see all the backup points you will need to restore at the Organizational level.

## Easy Connect

This project uses the Veeam Easy Connect https://github.com/shapedthought/veeam-easy-connect module.
