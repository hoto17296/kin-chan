import os
import logging

if os.environ.get('DEBUG'):
    logging.basicConfig(level=logging.DEBUG)

from aiohttp import web
from views import routes


app = web.Application()
app.add_routes(routes)


if __name__ == '__main__':
    web.run_app(app, port=80)