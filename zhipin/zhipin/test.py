# import requests
# from bs4 import BeautifulSoup

# with open(
#     "BOSS直聘-找工作上BOSS直聘直接谈！招聘求职找工作！.html", "r", encoding="utf-8"
# ) as f:
#     html = f.read()

# soup = BeautifulSoup(html, "html.parser")
# # 找到所有的dl class
# div_tags = soup.find_all("div", class_="menu-sub")

# jobs = []
# for div_tag in div_tags:
#     job = div_tag.find_all("div", class_="text")
#     for j in job:
#         jobs.extend(j.text.strip().split("\n"))


# with open("jobs.txt", "w", encoding="utf-8") as f:
#     for job in jobs:
#         f.write(job + "\n")

import json
from bs4 import BeautifulSoup

with open("zhipin.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")


# 找到<div class="wikiInfo-box" data-v-6da7a141="">
wiki_info_box = soup.find("div", class_="wikiInfo-box")
title = wiki_info_box.find("h1").text.strip()
# <div class="describe" data-v-6da7a141="">
description = wiki_info_box.find("div", class_="describe").text.strip()

contents = wiki_info_box.find_all("div", class_="list-wrap-item")
content = "\n".join([c.text.strip() for c in contents])


sec_body = soup.find_all("div", class_="sec-body")

month_list = sec_body[0].find("ul", class_="month-list")
month_list_items = month_list.find_all("li")
month = "\n".join([item.text.strip() for item in month_list_items])

year_list = sec_body[0].find("ul", class_="yaer-list")
year_list_items = year_list.find_all("li")
year = "\n".join([item.text.strip() for item in year_list_items])

skills_list = sec_body[1].find("ul", class_="skills-list")
skills_list_items = skills_list.find_all("li")
skills = "\n".join([item.text.strip() for item in skills_list_items])

list_wrap = sec_body[1].find("div", class_="part-show-list-wrap divide-class-list")
list_wrap_items = list_wrap.find_all("li")
delineations = []
for item in list_wrap_items:
    p = item.find_all("p")
    delineations.append(": ".join([i.text.strip() for i in p]))
delineation = "\n".join(delineations)

how = sec_body[1].find("div", class_="part-show-list-wrap content-list")
how_items = how.find_all("li")
how_list = []
for item in how_items:
    question = item.find("a").text.strip()

    # 找到 `<p>` 标签
    p_tag = item.find("p")

    # 提取 `<p>` 的文本，但移除 `<div>` 的内容
    for div in p_tag.find_all("div"):
        div.decompose()  # 移除 `<div>` 及其内容

    # 获取最终的纯文本
    answer = p_tag.get_text(strip=True)

    how_list.append(f"{question}\n{answer}\n")

how_list = "\n".join(how_list)

developments = sec_body[2].find_all("p", class_="question-title-content")
development_list = []
for development in developments:
    question = development.text.strip()
    development_list.append(question)

development_list = "\n".join(development_list)

interviews = sec_body[3].find_all("p", class_="question-title-content")
interview_list = []
for interview in interviews:
    question = interview.text.strip()
    interview_list.append(question)

interview_list = "\n".join(interview_list)

dic = {
    "职位": title,
    "描述": description,
    "工作内容": content,
    "月薪环比变化": month,
    "工作年限薪酬分布": year,
    "入门指南": {
        "从业条件": skills,
        "职业划分": delineation,
        "看看其他人如何入门的": how_list,
    },
    "职业成长": {
        "职业技能": development_list,
    },
    "求职面试": interview_list,
}

dic = json.dumps(dic, ensure_ascii=False, indent=4)
with open("zhipin.json", "w", encoding="utf-8") as f:
    f.write(dic)
