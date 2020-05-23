from os import getenv
import logging

if getenv('DEBUG'):
    logging.basicConfig(level=logging.DEBUG)

from aiohttp import web
import asyncpg
from views import routes
from slackapi import SlackAPI


async def startup(app: web.Application):
    app['pg'] = await asyncpg.create_pool(dsn=getenv('DATABASE_URL'))
    app['slack'] = SlackAPI(getenv('SLACK_API_TOKEN'), getenv('SLACK_SIGNING_SECRET'))

async def cleanup(app: web.Application):
    await app['pg'].close()


app = web.Application()

app.on_startup.append(startup)
app.on_cleanup.append(cleanup)

app.add_routes(routes)


if __name__ == '__main__':
    web.run_app(app, port=80)