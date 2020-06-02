from os import getenv
from logging import getLogger
from urllib.parse import parse_qsl
import json
from aiohttp import web
import aiojobs.aiohttp as aiojobs
from lib import fetch_data, check_activated, select_or_create_user
from slackapi import require_signature
import slack_view_templates


logger = getLogger()

routes = web.RouteTableDef()


# TODO cron 定義を修正
async def job(hhmm, app):
    # この時間に出勤リマインド設定しているユーザを検索
    query = 'SELECT id FROM users WHERE t_begin = $1 AND active IS TRUE'
    id_begin = [record['id'] for record in await app['pg'].fetch(query, hhmm)]
    logger.warn(id_begin)

    # この時間に退勤リマインド設定しているユーザを検索
    query = 'SELECT id FROM users WHERE t_end = $1 AND active IS TRUE'
    id_end = [record['id'] for record in await app['pg'].fetch(query, hhmm)]
    logger.warn(id_end)

    # 通知対象ユーザがいなければ終了
    if len(id_begin) == 0 and len(id_end) == 0:
        return

    # データをクロールする
    df = await fetch_data()
    logger.info(f'fetched {len(df)} rows')

    kingtime_url = 'https://s3.kingtime.jp/independent/recorder/personal/'

    # 出勤通知を送る
    df_begin = df[df['勤務日'] & (df['出勤時間'].isna())]
    text = f'出勤打刻を忘れていませんか？\n{kingtime_url}'
    for _, user in df_begin[df_begin['slack_user_id'].isin(id_begin)].iterrows():
        app['slack']['chat.postMessage'](channel=user['slack_user_id'], text=text, as_user=True)

    # 退勤通知を送る
    df_end = df[df['勤務日'] & (df['退勤時間'].isna())]
    text = f'退勤打刻を忘れていませんか？\n{kingtime_url}'
    for _, user in df_end[df_end['slack_user_id'].isin(id_end)].iterrows():
        app['slack']['chat.postMessage'](channel=user['slack_user_id'], text=text, as_user=True)


@routes.get(r'/schedule/{hh:\d\d}:{mm:\d\d}')
async def schedule(request):
    hhmm = request.match_info['hh'] + ':' + request.match_info['mm']
    await aiojobs.spawn(request, job(hhmm, request.app))
    return web.Response()


async def open_slack_modal_view(app, params):
    # ユーザの設定を取得する (該当ユーザがなければ作成する)
    user = await select_or_create_user(app['pg'], params['user_id'])
    logger.debug(user)
    # モーダルを開く
    view = slack_view_templates.activate(active=user['active'], t_begin=user['t_begin'], t_end=user['t_end'])
    app['slack']['views.open'](trigger_id=params['trigger_id'], view=view)


@routes.post('/slack/command')
@require_signature
async def slack_command(request):
    body = (await request.read()).decode()
    params = {k: v for k, v in parse_qsl(body)}

    if params['command'] != '/kingoftime-reminder':
        raise web.HTTPBadRequest()

    # TODO 対象じゃないユーザの場合、エラーメッセージを出す

    # views.open を待機しているとレスポンスが遅れてタイムアウトとなってしまうため、ジョブに回す
    await aiojobs.spawn(request, open_slack_modal_view(request.app, params))

    return web.Response()


@routes.post('/slack/interactive-endpoint')
@require_signature
async def slack_interactive_endpoint(request):
    body = (await request.read()).decode()
    data = json.loads({k: v for k, v in parse_qsl(body)}['payload'])
    slack_user_id = data['user']['id']

    # 設定の変更を DB に保存する
    if data['type'] == 'block_actions':
        assert len(data['actions']) == 1
        action = data['actions'][0]

        if action['action_id'] == 'active':
            active = len(action['selected_options']) > 0
            query = 'UPDATE users SET active = $1 WHERE id = $2'
            await request.app['pg'].execute(query, active, slack_user_id)
            logger.debug(f'{active=}')
        
        if action['action_id'] == 't_begin':
            t_begin = action['selected_option']['value']
            query = 'UPDATE users SET t_begin = $1 WHERE id = $2'
            await request.app['pg'].execute(query, t_begin, slack_user_id)
            logger.debug(f'{t_begin=}')
        
        if action['action_id'] == 't_end':
            t_end = action['selected_option']['value']
            query = 'UPDATE users SET t_end = $1 WHERE id = $2'
            await request.app['pg'].execute(query, t_end, slack_user_id)
            logger.debug(f'{t_end=}')

    return web.Response()