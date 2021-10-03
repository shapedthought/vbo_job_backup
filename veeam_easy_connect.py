import requests
from requests.auth import HTTPBasicAuth
import urllib3
urllib3.disable_warnings()
import getpass
import json


class VeeamEasyConnect():
    def __init__(self) -> None:
        self.em_port = 9398
        self.v11_port = 9419
        self.v11_headers = {"accept": "application/json",
                                    "x-api-version": "1.0-rev1", "Content-Type": "application/x-www-form-urlencoded"}
        self.v11_token_headers = {"accept": "application/json", "x-api-version": "1.0-rev1"} 
        self.vbo_headers = {"Content-Type": "application/json; charset=utf-8", "accept": "application/json"}
        self.em_headers = {"Accept": "application/json"}

    def vbo_login_base(self, address: str, username: str, password: str) -> list[dict]:
        self.vbo_address = address
        self.vbo_username = username
        self.vbo_password = password
        
        self.vbo_data = {"grant_type" : "password", "username": self.vbo_username, "password": self.vbo_password}
        self.vbo_login_url = f"https://{self.vbo_address}:4443/v5/Token"
        vbo_res = requests.post(self.vbo_login_url, data=self.vbo_data, headers=self.v11_headers, verify=False)
        vbo_res.raise_for_status()
        self.vbo_res_json = vbo_res.json()
        self.vbo_status_code = vbo_res.status_code
        self.vbo_token = self.vbo_res_json.get('access_token')
        self.vbo_headers['Authorization'] = 'Bearer ' + self.vbo_token
        return self.vbo_headers