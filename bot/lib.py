from logging import getLogger
from os import getenv
import urllib.request
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from kingtimesession import KingTimeSession
from slackapi import SlackAPI


logger = getLogger(__name__)


def fetch_slack_users(token: str) -> pd.DataFrame:
    slack_api = SlackAPI(token)
    body = slack_api['users.list']()
    assert body['ok']
    return pd.DataFrame([
        {
            'slack_user_id': u['id'],
            'メールアドレス': u['profile']['email'],
        }
        for u in body['members'] if 'email' in u['profile']
    ])


def parse(df, df_users: pd.DataFrame, df_slack_users: pd.DataFrame) -> pd.DataFrame:
    """タイムテーブルから必要な情報を抜き出す"""
    df = df[df['雇用区分'].str.contains('正社員')]
    df_parsed = df['名前'].str.split(n=1, expand=True)
    df_parsed.columns = ['ID', '名前']
    df_parsed['出勤時間'] = df['出勤'].str.extract(r'(\d+:\d+)')
    df_parsed['退勤時間'] = df['退勤'].str.extract(r'(\d+:\d+)')
    df_parsed['勤務日'] = (~df['スケジュール'].str.contains('休')) & (df['勤務日種別'] == '平日')
    return df_parsed.set_index('ID') \
        .join(df_users.set_index('従業員コード')[['メールアドレス']], how='left') \
        .merge(df_slack_users, how='left', on='メールアドレス')


async def fetch_data():
    # King of Time の管理画面をクロールする
    driver_opts = {
        'command_executor': getenv('SELENIUM_GRID_URL'),
        'desired_capabilities': DesiredCapabilities.CHROME,
    }
    with webdriver.Remote(**driver_opts) as driver:
        session = KingTimeSession(driver)
        session.login(getenv('KINGTIME_ADMIN_USERNAME'), getenv('KINGTIME_ADMIN_PASSWORD'))
        df = session.get_daily_working_list()
        session.move_to_top()
        df_users = session.get_user_list()
    logger.debug(f'fetched {len(df_users)} King of Time users data')

    # Slack のユーザ情報と結合する
    df_slack_users = fetch_slack_users(getenv('SLACK_API_TOKEN'))
    logger.debug(f'fetched {len(df_slack_users)} Slack users data')
    df_parsed = parse(df, df_users, df_slack_users)
    
    return df_parsed


async def check_activated(pg, slack_user_id) -> bool:
    query = 'SELECT COUNT(1) FROM users WHERE id = $1 AND active IS TRUE'
    return (await pg.fetchval(query, slack_user_id)) > 0
