from time import sleep
import pandas as pd


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