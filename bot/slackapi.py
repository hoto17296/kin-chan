from time import time
import urllib.request
import json
import hmac
import hashlib
from aiohttp.abc import AbstractView


class SlackAPI:
    
    def __init__(self, token: str, signing_secret: str = None, api_base: str = 'https://slack.com/api/'):
        self.token = token
        self.signing_secret = signing_secret
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

    def verify_signature(self, actual_sign: str, timestamp: int, body: bytes) -> bool:
        if abs(time() - int(timestamp)) > 60 * 5:
            return False
        req = 'v0:{}:'.format(timestamp).encode() + body
        expected_sign = 'v0=' + hmac.new(self.signing_secret.encode(), req, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sign, actual_sign)


# decorator
def require_signature(func):
    async def wrapper(*args, **kwargs):
        # Supports class based views
        request = args[0].request if isinstance(args[0], AbstractView) else args[0]
        if 'X-Slack-Signature' not in request.headers and 'X-Slack-Request-Timestamp' not in request.headers:
            raise web.HTTPUnauthorized()
        actual_sign = request.headers['X-Slack-Signature']
        timestamp = int(request.headers['X-Slack-Request-Timestamp'])
        body = await request.read()
        if not request.app['slack'].verify_signature(actual_sign, timestamp, body):
            raise web.HTTPUnauthorized()
        return await func(*args, **kwargs)
    return wrapper