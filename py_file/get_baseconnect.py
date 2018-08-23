# coding: utf-8

import requests
import time
import re
import os
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
from collections import Counter


def main():
    baseurl = "https://baseconnect.in"

    category_url = "/companies/category/63b80d21-f5eb-43d1-8c1c-ed1bf3a15cb5"

    # user agent
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0",
    }

    # カテゴリの取得
    category_dict = {}
    res = requests.get("http://baseconnect.in/", headers=headers)
    soup = BeautifulSoup(res.content, "html.parser")

    for item in soup.find("div", "home__category--left").find_all("li"):
        category_dict[re.sub(r"・$", "", item.p.string)] = baseurl+item.a.get("href")

    for item in soup.find("div", "home__category--right").find_all("li"):
        category_dict[re.sub(r"・$", "", item.p.string)] = baseurl+item.a.get("href")

    #### 業界の選択 ####
    for key, category_url in category_dict.items():
        if not key == "スポーツウェアショップ業界の会社": # test
            continue
        print(key)
        # 初期化
        page = 1
        last_flag = False
        df_all = pd.DataFrame()
        
        while True:
            url = category_url + "/" + str("?page=") + str(page)

            # ページの読み込み
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.content, "html.parser")
            time.sleep(3) # 遅延させる

            # 企業ページリストの取得
            lists = soup.find_all("div", "searches__result__list")
            address= [test.find("a").get("href") for test in lists]
            if len(address) == 0:
                print("-------- no list. DONE.")
                df_all.to_csv("./"+key+".csv")
                break

            #### 業界のリスト ####
            if soup.find(class_="next_page disabled") is None or last_flag is True:
                # ページ表示
                print("--- Getting data at page = {} ---".format(page))

                for target in tqdm(address):
                    # print(target)
                    # time.sleep(1)
                    res = requests.get(baseurl+target, headers=headers)
                    soup = BeautifulSoup(res.content, "html.parser")

                    # 会社名の抽出
                    basic_origin = {}

                    company_name = soup.find("h1", "node__header__text__title").get_text().strip()
                    company_kana = soup.find("div", "node__header__title__reading").get_text().strip()

                    basic_origin["会社名"] = company_name
                    basic_origin["会社名_ふりがな"] = company_kana

                    # 説明の抽出
                    company_title = soup.find("div", "node__header__cont__text--thumb").find("h2").get_text().strip()
                    company_abst = soup.find("div", "node__header__cont__text--thumb").find("p").get_text().strip()

                    basic_origin["会社概要_タイトル"] = company_title
                    basic_origin["会社概要_内容"] = company_abst

                    # タグの抽出
                    company_tag = soup.find("ul", "node__header__text__title__tag").get_text().strip().replace("\n", " ")
                    basic_origin["会社_タグ"] = company_tag

                    # 特徴と事業内容キーワード
                    company_keyword_character = soup.find("div", "node__header__tag__wrapper")
                    for content in company_keyword_character.find_all(class_="node__header__tag"):
                        if "事業内容" in content.find("h3").get_text():
                            company_key = content.find("ul").get_text().strip().replace("\n", " ")
                            basic_origin["会社_事業内容キーワード"] = company_key
                        if "特徴" in content.find("h3").get_text():
                            company_char = content.find("ul").get_text().strip().replace("\n", " ")
                            basic_origin["会社_特徴"] = company_char

                    basic_info2 = {}
                    rows = soup.find_all("dl")
                    for row in rows:
                        basic_info2[re.sub(r"\s+", "", row.dt.get_text())] = re.sub(r"\s+", "", row.dd.get_text())

                    try:
                        basic_info2["代表者_名前"] = basic_info2.pop("名前")
                    except KeyError:
                        pass
                    try:
                        basic_info2["代表者_出身大学"] = basic_info2.pop("出身大学")
                    except KeyError:
                        pass
                    try:
                        basic_info2["代表者_生年月日"] = basic_info2.pop("生年月日")
                    except KeyError:
                        pass


                    # 代表者
                    basic_officer_all = {}
                    soup_tmp = soup.find("div", "node__officer")
                    if soup_tmp:
                        rows = soup_tmp.find_all(class_="nodeTable--desc")
                        for index, row in enumerate(rows):
                            basic_officer = {}
                            tmp = re.sub(r"\s+", " ", row.find("h3").get_text().strip().replace("\n", "")).split(" ")
                            basic_officer["氏名"], basic_officer["役職"] = tmp[0], ''.join(tmp[1:])
                            basic_officer["プロフィール"] = re.sub(r"\s+", "", row.find(class_="nodeTable--desc__desc").get_text().strip())    
                            basic_officer_all["役員_"+str(index).zfill(2)] = basic_officer


                    # 連絡先
                    basic_contact = {}
                    soup_tmp = soup.find("div", "node__contact")
                    if soup_tmp:
                        for item in soup_tmp.find_all("a"):
                            tmp = re.sub(r"\s+", "", item.get_text())
                            if "会社" in tmp:
                                basic_contact[tmp] = item.get("href")
                            elif "お問い合わせ" in tmp:
                                basic_contact[tmp] = item.get("href")


                    # ランキング
                    basic_rank = {}
                    soup_tmp = soup.find("div", "nodeRank")
                    if soup_tmp:
                        title = soup_tmp.find(class_="nodeRank__heading").string
                        for list_item in soup_tmp.find_all("li"):
                            tmp = re.sub(r"\s+", "", list_item.get_text())
                            rank, genre = re.search(r"(.*)(\(.*?\))", tmp).groups()
                            basic_rank[title+genre] = rank

                    soup_tmp = soup.find("div", "nodeRank--other")
                    if soup_tmp:
                        title = soup_tmp.find(class_="nodeRank__heading").string
                        for list_item in soup_tmp.find_all("li"):
                            tmp = re.sub(r"\s+", "", list_item.get_text())
                            rank, genre = re.search(r"(.*)(\(.*?\))", tmp).groups()
                            basic_rank[title+genre] = rank



                    basic_origin.update(basic_info2)
                    basic_origin.update(basic_officer_all)
                    basic_origin.update(basic_contact)
                    basic_origin.update(basic_rank)

                    # データフレームに格納
                    df = pd.io.json.json_normalize(basic_origin)
                    try:
                        df_all = pd.concat([df_all, df])
                    except NameError:
                        df_all = pd.io.json.json_normalize(basic_origin)
                # ページの追加
                page += 1

                if last_flag:
                    df_all.to_csv("./"+key+".csv")
                    print("--- DONE ---")
                    break
            else:
                if last_flag is True:
                    break
                else:
                    last_flag = True
        

if __name__ == '__main__':
    save_dir = "./out_base"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    main()
