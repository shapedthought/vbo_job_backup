import requests
from requests.auth import HTTPBasicAuth
import urllib3
urllib3.disable_warnings()
import getpass
import json
import logging

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')


class VeeamEasyConnect():
    def __init__(self) -> None:
        self.em_port = 9398
        self.v11_port = 9419
        self.v11_headers = {"Accept": "application/json",
                                    "x-api-version": "1.0-rev1", "Content-Type": "application/x-www-form-urlencoded"}
        self.v11_token_headers = {"accept": "application/json", "x-api-version": "1.0-rev1"} 
        self.ma_headers = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
        self.vbo_headers = {"Content-Type": "application/json; charset=utf-8", "accept": "application/json"}
        self.em_headers = {"Accept": "application/json"}

    def vbo_login_base(self, address: str, username: str, password: str) -> list[dict]:
        self.vbo_address = address
        self.vbo_username = username
        self.vbo_password = password
        
        self.vbo_data = {"grant_type" : "password", "username": self.vbo_username, "password": self.vbo_password}
        self.vbo_login_url = f"https://{self.vbo_address}:4443/v5/Token"
        vbo_res = requests.post(self.vbo_login_url, data=self.vbo_data, headers=self.ma_headers, verify=False)
        vbo_res.raise_for_status()
        self.vbo_res_json = vbo_res.json()
        self.vbo_status_code = vbo_res.status_code
        self.vbo_token = self.vbo_res_json.get('access_token')
        self.vbo_headers['Authorization'] = 'Bearer ' + self.vbo_token
        return self.vbo_headers

    def modern_auth(self, tenant: str, client_id: str) -> dict:
        self.client_id = client_id
        self.tenant = tenant
        self.auth_url = f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/devicecode"
        self.auth_body = {"client_id" : self.client_id, "scope": "Directory.AccessAsUser.All User.ReadWrite.All offline_access"}
        aut_res = requests.post(self.auth_url, data=self.auth_body, headers=self.ma_headers, verify=False)
        aut_res.raise_for_status()
        auth_jason = aut_res.json()
        self.device_code = auth_jason.get("device_code")
        return aut_res.json()

    def oauth_token(self) -> dict:
        self.oauth_url = f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/token"
        self.oauth_body = {"grant_type" : "urn:ietf:params:oauth:grant-type:device_code", "client_id": self.client_id, "device_code": self.device_code}
        self.token_res = requests.post(self.oauth_url, data=self.oauth_body, headers=self.ma_headers, verify=False)
        self.token_res.raise_for_status()
        self.token_json = self.token_res.json()
        return self.token_res.json()
    
    def ma_vbo_login(self, address: str) -> dict:
        self.vbo_address = address
        self.vbo_login_url = f"https://{self.vbo_address}:4443/v5/token"
        self.ma_login_body = {"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "client_id": self.tenant, "assertion": self.token_json}
        login_res = requests.post(self.vbo_login_url, data=self.ma_login_body, headers=self.v11_headers, verify=False)
        login_res.raise_for_status()
        self.login_json = login_res.json()
        return self.login_json