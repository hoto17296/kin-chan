import os
from logging import getLogger
from aiohttp import web
from lib import fetch_data
from slackapi import SlackAPI


logger = getLogger()

routes = web.RouteTableDef()


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
    email = os.environ.get('DEBUG_USER_EMAIL')
    if os.environ.get('DEBUG') and email:
        df = df[df['メールアドレス'] == email]

    # リマインド対象を絞り込む
    mode = request.match_info['mode']
    logger.debug(f'mode: {mode}')
    kingtime_url = 'https://s3.kingtime.jp/independent/recorder/personal/'
    if request.match_info['mode'] == 'begin':
        text = f'出勤打刻を忘れていませんか？\n{kingtime_url}'
        # df = df[df['勤務日'] & (df['出勤時間'].isna())]
    else:
        text = f'退勤打刻を忘れていませんか？\n{kingtime_url}'
        # df = df[df['勤務日'] & (df['退勤時間'].isna())]

    # リマインドを送信
    logger.debug(f'send remind message to below users')
    logger.debug(df)
    slack_api = SlackAPI(os.environ.get('SLACK_API_TOKEN'))
    for _, row in df.iterrows():
        slack_api['chat.postMessage'](channel=row['slack_user_id'], text=text, as_user=True)