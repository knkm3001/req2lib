#!/usr/bin/env python
# coding: utf-8
import re
import sys
import argparse
import traceback
from time import sleep
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import chromedriver_binary

# selenium用
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains

# 環境変数用ファイル
import env

# 引数デフォルト処理
HEADLESS_FLG = False

# コマンドライン引数の設定
description = " auto request opac tumsat "
parser = argparse.ArgumentParser(description=description)
parser.add_argument('-hl','--headless' ,
                       action='store_true' ,
                       help='chromeをヘッドレスモードで実行')
args = parser.parse_args()

# コマンドライン引数の対応
if args.headless:
    HEADLESS_FLG = True

print("HEADLESS_FLG: ",HEADLESS_FLG)


AMAZON_WISHLIST_URL = env.AMAZON_WISHLIST_URL
REASON_FOR_PURCHASE = env.REASON_FOR_PURCHASE
TUMSAT_OPAC_URL = env.TUMSAT_OPAC_URL
OPAC_ID = env.OPAC_ID
OPAC_PW = env.OPAC_PW

if not (AMAZON_WISHLIST_URL and REASON_FOR_PURCHASE and OPAC_ID and OPAC_PW):
    print("変数が正しくありません")
    sys.exit()


def set_in_webdriver():
    """
    webdriver(chrome) の設定
    """
    options = webdriver.ChromeOptions()
    if HEADLESS_FLG:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')

    # SSLセキュリティ証明書のエラーページを表示しない
    options.add_argument('--no-sandbox')
    # 共有メモリファイルを/dev/shmではなく/tmpでつかう
    options.add_argument('--disable-dev-shm-usage')
    # ブラウザ言語
    options.add_argument('--lang=ja')
    # ユーザ－エージェント
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36 "
    options.add_argument(f'user-agent={user_agent}')
    # 拡張機能無効
    options.add_argument('--disable-extensions')
    # ウィンドウ最大化
    options.add_argument('--start-maximized')
    # プロキシ設定
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")

    driver = webdriver.Chrome(chrome_options=options)

    return driver


def main():
    """
    main処理

    amazonの欲しい物リストから書籍リストを取得
    そのあとOPAC(図書館サイト)へアクセスして書籍リストのものを入力しリクエスト
    """

    # selenium 立ち上げ
    driver = set_in_webdriver()

    driver.get(AMAZON_WISHLIST_URL)

    # 欲しい物リストをページ下部まで表示させる
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(1)
    driver.execute_script("window.scrollTo(0, 0);")

    wish_books = []

    html_source = driver.page_source
    baseurl = driver.current_url
    soup = BeautifulSoup(html_source,"html.parser")
    # itemName_ABC123DEF456GH みたいなidをもつ要素が商品名(とそのページへのリンク)
    wishitem_arr =  [elem for elem in soup.find_all(id=re.compile(r'itemName_[0-9A-Z]+'))]

    for wishitem in wishitem_arr:
        sleep(1)
        wishitem_url = urljoin(baseurl,wishitem.get("href"))

        driver.execute_script("window.open()")
        driver.switch_to.window(driver.window_handles[1])

        driver.get(wishitem_url)

        wish_book_info = get_wish_book_info(driver)
        if wish_book_info:
            wish_books.append(wish_book_info)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    driver.get(TUMSAT_OPAC_URL)

    elem_id_form = driver.find_element_by_xpath('//*[@id="userid"]')
    elem_id_form.send_keys(OPAC_ID)

    elem_id_form = driver.find_element_by_xpath('//*[@id="p_check_text_pass"]')
    elem_id_form.send_keys(OPAC_PW)

    driver.find_element_by_xpath('//*[@id="opac_login_disp"]/p[2]/input[1]').click()

    # 今までのリクエストを確認
    try:
        driver.get('https://lib.s.kaiyodai.ac.jp/opac/bok_req/?lang=0&reqCode=list&phasecd=ALL&range=A&oh_flg=1')
        selector = driver.find_element_by_xpath('//*[@id="example_length"]/select')
        Select(selector).select_by_value('200') # 200冊表示
        requested_books = driver.find_elements_by_xpath('//td[contains(@class, "max_width bokreq_tr")]')
        requested_titles = [requested_book.text for requested_book in requested_books]
    except:
        requested_titles = []

    # 次に検索
    for wish_book in wish_books:
        sleep(1)
        print(f"\nリクエスト書籍名: {wish_book.get('book_title')}")

        driver.get('https://lib.s.kaiyodai.ac.jp/opac/opac_search/?lang=0')
        if wish_book.get('book_title') in requested_titles: # 重複リクエスト防止
            print("すでにリクエスト済みです")
            continue

        print("蔵書から書籍を検索")

        if wish_book.get('isbn-13'):
            q_word = wish_book.get('isbn-13')
        elif wish_book.get('isbn-10'):
            q_word = wish_book.get('isbn-10')
        else:
            print(f"ISBNコードが取得できなかったので検索できませんでした")
            continue

        driver.find_element_by_xpath('//*[@id="text_kywd"]').send_keys(q_word)
        driver.find_element_by_xpath('//*[@id="simple_panel"]/p/span/a[1]').click()
        sleep(1)

        # ISBNコードで検索して蔵書に存在してたらリクエストしない
        if driver.find_elements_by_xpath("//*[contains(@class, 'slist wi100P')]"):
            print('検索した結果、図書館にあったのでリクエストしません')
            continue
        else:
            nobook_mssg = driver.find_element_by_xpath("//*[contains(@class, 'sta-info ui-corner-all clearfix')]").text
            if nobook_mssg and '該当する資料が学内に見つかりません。' in nobook_mssg:
                print("図書館にないのでリクエストします")
                request_wish_book(driver,wish_book)
                print("リクエストしました!")
            else:
                pass

    # headless mode じゃなければ、最後はリクエスト一覧画面へ
    if not HEADLESS_FLG:
        driver.get('https://lib.s.kaiyodai.ac.jp/opac/bok_req/?lang=0&reqCode=list&phasecd=ALL&range=A&oh_flg=1')
        selector = driver.find_element_by_xpath('//*[@id="example_length"]/select')
        Select(selector).select_by_value('200')


def get_wish_book_info(driver):
    """
    amazonの個々の商品ページから商品の詳細を取得し、変数wish_book_infoにまとめる
    """

    category_elem = driver.find_element_by_xpath('//*[@id="wayfinding-breadcrumbs_feature_div"]/ul/li[1]/span/a')

    # まず"本"であること
    if not "本" in category_elem.text:
        wish_book_info = None
    else:
        wish_book_info = dict()
        book_title = driver.find_element_by_xpath('//*[@id="productTitle"]').text
        wish_book_info['book_title'] = book_title
        print(f"リクエスト書籍に追加: ",book_title)
        other_book_info = driver.find_element_by_xpath('//div[@id="detail_bullets_id"]').text
        for text_info in other_book_info.split("\n"):
            if "出版社:" in text_info:
                wish_book_info['publisher'] = text_info.replace('出版社: ','')
            elif "ISBN-10:" in text_info:
                wish_book_info['isbn-10'] = text_info.replace('ISBN-10: ','')
            elif "ISBN-13:" in text_info:
                wish_book_info['isbn-13'] = text_info.replace('ISBN-13: ','')
            elif "発売日：" in text_info:
                wish_book_info['p_date'] = text_info.replace('発売日： ','')
    return wish_book_info


def request_wish_book(driver,wish_book):
    """
    リクエストフォームの入力
    """

    driver.get('https://lib.s.kaiyodai.ac.jp/opac/bok_req/?lang=0')

    # ISBN 必須項目
    isbn_code = wish_book.get('isbn-13') if wish_book.get('isbn-13') else wish_book.get('isbn-10')
    driver.find_element_by_xpath('//*[@id="isbn"]').send_keys(isbn_code)

    # タイトル 必須項目
    driver.find_element_by_xpath('//*[@id="tr"]').send_keys(wish_book.get('book_title'))

    # 出版社 必須項目
    driver.find_element_by_xpath('//*[@id="pub"]').send_keys(wish_book.get('publisher'))

    # 出版年
    if wish_book.get('p_date'):
        pyear = wish_book.get('p_date')[0:4]
        driver.find_element_by_xpath('//*[@id="pyear"]').send_keys(pyear)

    # 購入理由 必須項目
    driver.find_element_by_xpath('//*[@id="dmdcrspnd"]').send_keys(REASON_FOR_PURCHASE)

    # リクエスト申請(2回とも同じxpath)
    driver.find_element_by_xpath("//*[contains(@class, 'btn_lead')]").click()
    driver.find_element_by_xpath("//*[contains(@class, 'btn_lead')]").click()





if __name__ == '__main__':
    main()

