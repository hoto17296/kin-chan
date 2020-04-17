import os
import re
from time import sleep
from datetime import date
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import slack


class KingTimeSession:

    def __init__(self, driver):
        self.driver = driver

    def login(self, username, password):
        """ログイン情報を入力してログイン"""
        self.driver.get('https://s3.kingtime.jp/admin')
        self.driver.find_element_by_id('login_id').send_keys(username)
        self.driver.find_element_by_id('login_password').send_keys(password)
        self.driver.find_element_by_class_name('login_button').click()
        sleep(1)
        # Welcome メッセージを消す
        self.driver.execute_script('var el = document.getElementsByClassName("htBlock-dialog_wrapper"); if (el.length > 0) el[0].remove()')
        
    def move_to_top(self):
        # トップページに飛ぶ
        self.driver.find_element_by_class_name('htBlock-header_homeButton').find_element_by_tag_name('a').click()
        sleep(1)
        # Welcome メッセージを消す
        self.driver.execute_script('var el = document.getElementsByClassName("htBlock-dialog_wrapper"); if (el.length > 0) el[0].remove()')
        
    def get_daily_working_list(self):
        """日別データを取得"""
        # メニューから「日別データ」に飛ぶ
        self.driver.find_element_by_id('header_main_menu').find_element_by_link_text('全メニュー').click()
        sleep(0.5)
        self.driver.find_element_by_class_name('htBlock-header_menuBody').find_element_by_link_text('日別データ').click()
        sleep(1)
        # 「表示」ボタンをクリック
        self.driver.find_element_by_id('display_button').click()
        sleep(1)
        # テーブルを読み込んで DataFrame に変換
        table = self.driver.find_element_by_id('tab-1').find_element_by_tag_name('table')
        columns = [th.text.replace('\n', '') for th in table.find_element_by_tag_name('thead').find_elements_by_tag_name('th')]
        data = [[td.text for td in th.find_elements_by_tag_name('td')] for th in table.find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')]
        return pd.DataFrame(data, columns=columns)
    
    def get_user_list(self):
        """従業員リストを取得"""
        # 従業員設定ページに飛ぶ
        self.driver.get(self.driver.current_url.split('?')[0] + '?page_id=/setup/employee_list')
        # テーブルを読み込んで DataFrame に変換
        table = self.driver.find_element_by_class_name('htBlock-mainContents').find_element_by_tag_name('table')
        columns = [th.text.replace('\n', '') for th in table.find_element_by_tag_name('thead').find_elements_by_tag_name('th')]
        data = [[td.text for td in th.find_elements_by_tag_name('td')] for th in table.find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')]
        return pd.DataFrame(data, columns=columns)


async def fetch_slack_users(client):
    users = (await client.users_list()).data['members']
    return pd.DataFrame([
        {
            'slack_user_id': u['id'],
            'メールアドレス': u['profile']['email'],
        }
        for u in users if 'email' in u['profile']
    ])


def parse(df, df_users, df_slack_users):
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


if __name__ == '__main__':
    options = {
        'command_executor': os.environ.get('SELENIUM_GRID_URL'),
        'desired_capabilities': DesiredCapabilities.CHROME,
    }
    with webdriver.Remote(**options) as driver:
        session = KingTimeSession(driver)
        session.login(os.environ.get('KINGTIME_ADMIN_USERNAME'), os.environ.get('KINGTIME_ADMIN_PASSWORD'))
        df = session.get_daily_working_list()
        session.move_to_top()
        df_users = session.get_user_list()

    slack_client = slack.WebClient(os.environ.get('SLACK_API_TOKEN'), run_async=True)

    df_slack_users = await fetch_slack_users(slack_client)

    df_parsed = parse(df, df_users, df_slack_users)

    # TODO send message