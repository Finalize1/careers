import re
import os
import json
import scrapy
from bs4 import BeautifulSoup
import numpy as np


class JdjywSpider(scrapy.Spider):
    name = "jdjyw"
    allowed_domains = ["jdjyw.jlu.edu.cn"]
    start_urls = [
        "https://jdjyw.jlu.edu.cn/portal/jyzp/recruit/list?type=1&pageNo=1&pageSize=12"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.first_item = True
        if os.path.exists("crawled_urls.txt"):
            with open("crawled_urls.txt", "r", encoding="utf-8") as f:
                self.existing_url = f.read().splitlines()
        else:
            self.existing_url = []

    def parse(self, response):
        # 解析当前页面的招聘信息
        for item in response.css(".m-list-line"):
            li_list = item.css("li")
            for li in li_list:
                url = li.css("a::attr(href)").get()
                title = li.css("a::text").get()
                if url and (url not in self.existing_url):
                    self.existing_url.append(url)
                    yield response.follow(
                        url, callback=self.parse_more, meta={"title": title}
                    )

        # 翻页处理
        current_page = int(response.url.split("pageNo=")[1].split("&")[0])
        if current_page < 121:
            next_page = current_page + 1
            next_url = f"https://jdjyw.jlu.edu.cn/portal/jyzp/recruit/list?type=1&pageNo={next_page}&pageSize=12"
            yield scrapy.Request(next_url, callback=self.parse)

    def parse_more(self, response):
        def clean_whitespace(value):
            if isinstance(value, str):
                return " ".join(re.sub(r"\s+", " ", value).strip().split())
            elif isinstance(value, dict):
                return {k: clean_whitespace(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [clean_whitespace(v) for v in value]
            return value

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="m-detail-table-1")
        dic = {}

        dic["标题"] = response.meta.get("title", "").strip()
        dic["url"] = response.url.strip()

        rows = table.find_all("tr")

        for row in rows:
            th = row.find_all("th")
            td = row.find_all("td")
            for h, d in zip(th, td):
                dic[h.text.strip()] = d.text.strip()
        if "单位地址" in dic:
            del dic["单位地址"]
        if "单位规模" in dic:
            del dic["单位规模"]
        if "单位网址" in dic:
            del dic["单位网址"]

        plan = soup.find("table", class_="m-detail-table-2")
        th = plan.find_all("th")
        td = plan.find_all("td")
        plan = {}
        for h, d in zip(th, td):
            plan[h.text.strip()] = d.text.strip()
        dic["计划"] = plan

        if soup.find("table", class_="m-detail-table-3"):
            plan3 = soup.find("table", class_="m-detail-table-3")
            th = [h.text.strip() for h in plan3.find_all("th")]
            td = [d.text.strip() for d in plan3.find_all("td")]

            # 将一维列表转为二维（每行len(th)列）
            td_reshaped = np.array(td).reshape(-1, len(th))
            details = []
            for row in td_reshaped:
                detail = dict(zip(th, row))  # 直接用zip组合表头和行数据
                details.append(detail)
            dic["职位"] = details
        else:
            # 找到m-detail-content__container里的table
            table = soup.find("div", class_="m-detail-content__container").find("table")
            if table:
                # 找到firstRow的tr以及下一个tr
                first_row = table.find("tr", class_="firstRow")
                next_row = first_row.find_next_sibling("tr")
                first_row_text = [
                    td.get_text(strip=True) for td in first_row.find_all("td")
                ]
                next_row_text = [
                    td.get_text(strip=True) for td in next_row.find_all("td")
                ]

                careers = []
                if len(first_row_text) >= len(next_row_text):
                    header = first_row_text
                    length = len(first_row_text)
                    all_rows = first_row.find_next_siblings("tr")
                else:
                    header = next_row_text
                    length = len(next_row_text)
                    all_rows = next_row.find_next_siblings("tr")

                all_rows_text = [
                    [td.get_text(strip=True) for td in row.find_all("td")]
                    for row in all_rows
                ]
                first_column = all_rows_text[0][0]
                for row in all_rows_text:
                    career = {}
                    if len(row) < length:
                        row.insert(0, first_column)
                        for h, r in zip(header, row):
                            career[h] = r
                        careers.append(career)
                    else:
                        first_column = row[0]
                        for h, r in zip(header, row):
                            career[h] = r
                        careers.append(career)
                dic["职位"] = careers
            else:
                dic["职位"] = ""

        detail_content = soup.find("div", class_="m-detail-content__container")
        if detail_content:
            text = detail_content.get_text()

            people_parents = []
            for text in detail_content.find_all(text=re.compile("联系人")):
                parent = text.find_parent(["p", "td"])
                if parent:
                    people_parents.append(parent.get_text(strip=True, separator=" "))

            # 将结果存入字典
            dic["联系人"] = people_parents
        else:
            dic["联系人"] = ""

        detail_content = soup.find("div", class_="m-detail-content__container")
        if detail_content:
            text = detail_content.get_text()

            phone_parents = []
            for text in detail_content.find_all(
                text=re.compile(r"(?:\+?86)?1[3-9]\d{9}|(?:\d{3,4}-)?\d{7,8}")
            ):
                parent = text.find_parent(["p", "td"])
                if parent:
                    phone_parents.append(parent.get_text(strip=True, separator=" "))

            # 将结果存入字典
            dic["联系方式"] = phone_parents
        else:
            dic["联系方式"] = ""

        detail_content = soup.find("div", class_="m-detail-content__container")
        if detail_content:
            text = detail_content.get_text()

            wechat_parents = []
            for text in detail_content.find_all(text=re.compile(r"微信")):
                parent = text.find_parent(["p", "td"])
                if parent:
                    wechat_parents.append(parent.get_text(strip=True, separator=" "))

            # 将结果存入字典
            dic["微信"] = wechat_parents
        else:
            dic["微信"] = ""

        dic = clean_whitespace(dic)

        if "招聘时间" in dic:
            del dic["招聘时间"]
        if "招聘地点" in dic:
            del dic["招聘地点"]

        yield dic

    def closed(self, reason):
        with open("crawled_urls.txt", "w", encoding="utf-8") as f:
            for url in self.existing_url:
                f.write(url + "\n")
