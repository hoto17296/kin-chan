from os import getenv
from logging import getLogger
from urllib.parse import parse_qsl
import json
from aiohttp import web
from lib import fetch_data, check_activated, select_or_create_user
from slackapi import require_signature
import slack_view_templates


logger = getLogger()

routes = web.RouteTableDef()


# TODO 時間を受け取るようにエンドポイントを修正 (cron も)
@routes.get(r'/{mode:(begin|end)}')
async def handler(request):
    # 先に HTTP レスポンスを返しておく
    response = web.Response()
    await response.prepare(request)
    await response.write_eof()

    # データをクロールする
    df = await fetch_data()
    logger.debug(f'fetched {len(df)} rows')

    # 開発中は特定のユーザ以外にはリマインドを送らないようにする
    email = getenv('DEBUG_USER_EMAIL')
    if getenv('DEBUG') and email:
        df = df[df['メールアドレス'] == email]

    # TODO この時間にリマインド設定しているユーザがいない場合は終了

    # リマインド対象を絞り込む
    mode = request.match_info['mode']
    logger.debug(f'mode: {mode}')
    kingtime_url = 'https://s3.kingtime.jp/independent/recorder/personal/'
    if request.match_info['mode'] == 'begin':
        text = f'出勤打刻を忘れていませんか？\n{kingtime_url}'
        df = df[df['勤務日'] & (df['出勤時間'].isna())]
    else:
        text = f'退勤打刻を忘れていませんか？\n{kingtime_url}'
        df = df[df['勤務日'] & (df['退勤時間'].isna())]

    # リマインドを送信
    # TODO この時間にリマインド設定しているユーザのみに通知するように変更
    logger.debug(f'send remind message to below users')
    logger.debug(df)
    for _, row in df.iterrows():
        request.app['slack']['chat.postMessage'](channel=row['slack_user_id'], text=text, as_user=True)


@routes.post('/slack/command')
@require_signature
async def slack_command(request):
    body = (await request.read()).decode()
    params = {k: v for k, v in parse_qsl(body)}

    if params['command'] == '/kingoftime-reminder':
        # TODO 対象じゃないユーザの場合、エラーメッセージを出す
        # Send Response
        response = web.Response()
        await response.prepare(request)
        await response.write_eof()
        # ユーザの設定を取得する (該当ユーザがなければ作成する)
        user = await select_or_create_user(request.app['pg'], params['user_id'])
        logger.debug(user)
        # Modal View を開く
        view = slack_view_templates.activate(active=user['active'], t_begin=user['t_begin'], t_end=user['t_end'])
        request.app['slack']['views.open'](trigger_id=params['trigger_id'], view=view)
        return response
    else:
        raise web.HTTPBadRequest()


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