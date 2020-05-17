import urllib.request
import json


class SlackAPI:
    
    def __init__(self, token: str, api_base: str = 'https://slack.com/api/'):
        self.token = token
        self.api_base = api_base
    
    def __call__(self, name: str, charset: str = 'utf-8', **kwargs) -> dict:
        req = urllib.request.Request(
            url = self.api_base + name,
            data = json.dumps(kwargs).encode(charset),
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': f'application/json; charset={charset}',
            })
        with urllib.request.urlopen(req) as res:
            return json.load(res)
    
    def __getitem__(self, key: str):
        return lambda **kwargs: self(key, **kwargs)