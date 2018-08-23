# coding: utf-8

import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
import os

save_dir = "./out_nico"

def main():
    # 本番
    baseUrl = "https://nicoly.jp/clinic/"
    # user agent指定
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0",
    }

    df_all = pd.DataFrame()

    for i in tqdm(range(1, 3500)):
        url = baseUrl + str(i)

        if i % 100 == 0:
            time.sleep(10)
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, "html.parser")
            table = soup.find_all("table")[0]
            rows = table.find_all("tr")

            dict = {}
            for row in rows:
                key = row.th.get_text()
                tmp = re.sub(r"※.*", "", row.td.get_text())
                tmp = re.sub(r"\s+", " ", tmp)
                tmp = re.sub(r"\s+$", "", tmp)
                dict[key] = tmp

                if row.td.a:
                    dict[key] = row.td.a.get("href")

            df = pd.io.json.json_normalize(dict)

            try:
                df_all = pd.concat([df_all, df])
            except NameError:
                df_all = pd.io.json.json_normalize(dict)

    df_all.to_csv("./out_nico/nico_all.csv")


if __name__ == '__main__':
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    main()
