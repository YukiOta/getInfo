# coding: utf-8

import requests
import time
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
import os


def main():
    # ドメイン
    base_url = "https://medley.life"
    # target_url = "/institutions/pref_北海道/?page="

    # user agent
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0",
    }

    prefs = ['北海道', '青森県', '岩手県', '宮城県', '秋田県',
             '山形県', '福島県', '茨城県', '栃木県', '群馬県',
             '埼玉県', '千葉県', '東京都', '神奈川県', '新潟県',
             '富山県', '石川県', '福井県', '山梨県', '長野県',
             '岐阜県', '静岡県', '愛知県', '三重県', '滋賀県',
             '京都府', '大阪府', '兵庫県', '奈良県', '和歌山県',
             '鳥取県', '島根県', '岡山県', '広島県', '山口県',
             '徳島県', '香川県', '愛媛県', '高知県', '福岡県',
             '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県',
             '鹿児島県', '沖縄県']

    for pref in prefs:
        target_url = "/institutions/pref_" + pref + "/?page="
        # 初期化
        df_all = pd.DataFrame()
        page = 1
        last_flag = False

        while True:
            url = base_url + target_url + str(page)
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")

            if soup.find(class_="o-pagination__next") is not None or last_flag is True:
                # ページ表示
                print("--- Getting data at page = {} ---".format(page))
                time.sleep(3)  # 遅延させる

                hospitals = soup.find_all("li", "c-search-item")

                # hospital内探索
                for hospital in tqdm(hospitals):
                    toadd = {}

                    hospital_url = hospital.find("a").get("href")
                    hospital_type = hospital.find("label").get_text().strip()
                    toadd["タイプ"] = hospital_type
                    # time.sleep(1)
                    # 病院ページにアクセス
                    res = requests.get(base_url + hospital_url, headers=headers)
                    soup = BeautifulSoup(res.text, "html.parser")

                    rows = soup.find_all("table")[0].find_all("tr")

                    for row in rows:
                        toadd[row.th.get_text()] = row.td.get_text()

                    # 診療科と専門外来を追加
                    for section in soup.find_all("section"):
                        if "診療科" in section.find("header").get_text().strip():
                            departments = section.find_all("a")
                            tmp = [department.get_text().strip()
                                for department in departments]
                            toadd["診療科"] = " ".join(tmp)

                        if "専門外来" in section.find("header").get_text().strip():
                            outpatients = section.find_all("label")
                            tmp = [outpatient.get_text().strip()
                                for outpatient in outpatients]
                            toadd["専門外来"] = " ".join(tmp)

                    # データフレームに格納
                    df = pd.io.json.json_normalize(toadd)
                    try:
                        df_all = pd.concat([df_all, df])
                    except NameError:
                        df_all = pd.io.json.json_normalize(toadd)

                page += 1

                if last_flag:
                    df_all.to_csv("./" + pref + ".csv")
                    print("--- DONE. ---")
                    break
            else:
                if last_flag is True:
                    break
                else:
                    last_flag = True


if __name__ == '__main__':
    save_dir = "./out_med"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    main()
