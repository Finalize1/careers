import os
import time
import json

from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
import concurrent.futures


def save_cookies(driver, filename):
    """保存 Cookies（包含 domain/path）"""
    cookies = driver.get_cookies()
    with open(filename, "w") as f:
        json.dump(cookies, f)  # 保存完整 Cookies 信息


def load_cookies(driver, filename):
    """加载 Cookies（确保 domain/path 正确）"""
    with open(filename, "r") as f:
        cookies = json.load(f)
    driver.get("https://daquan.yl1001.com/zhiye")  # 先访问根域名
    for cookie in cookies:
        # 确保 Cookies 能作用于所有子页面
        if "domain" not in cookie:
            cookie["domain"] = ".daquan.yl1001.com"  # 通配符域名
        driver.add_cookie(cookie)


def visit_urls(job):
    # Create a new instance of the Chrome driver
    driver = webdriver.Edge()

    # Navigate to the website you want to scrape
    driver.get("https://daquan.yl1001.com")
    load_cookies(driver, "../cookies.json")
    driver.refresh()

    try:
        dic = {}

        dic["职业类别"] = job["类别"]
        dic["职业名称"] = job["职业名称"]
        dic["职业描述"] = job["职业描述"]
        dic["url"] = job["url"]
        driver.get(job["url"])

        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.nuxt-page")))

        soup = BeautifulSoup(driver.page_source, "html.parser")
        introduction = soup.find("div", class_="sub-item introduction")
        content_text = introduction.find("div", class_="content-text").get_text(
            strip=True
        )
        dic["职位定义"] = content_text

        # sub-item anchor-title
        anchor_title = soup.find("div", class_="sub-item anchor-title")
        # main-work-content
        main_work_content = anchor_title.find(
            "div", class_="main-work-content"
        ).get_text(strip=True, separator="\n")
        dic["主要工作内容"] = main_work_content

        # card-wrap-1
        card_wrap_1 = soup.find("section", class_="card-wrap-1")

        sub_items = card_wrap_1.find("div", class_="sub-item")
        first_child_list = sub_items.find("div", class_="first-child-list")
        first_child_items = first_child_list.find_all("div", class_="first-child-item")
        for item in first_child_items:
            title = item.find("div", class_="first-child-description").get_text(
                strip=True
            )
            content = item.find("div", class_="first-child-value").get_text(strip=True)
            dic[title] = content

        work_place_and_guard = soup.find("div", class_="sub-item work-place-and-guard")
        first_child_list = work_place_and_guard.find("div", class_="first-child-list")
        first_child_items = first_child_list.find_all("div", class_="first-child-item")
        for item in first_child_items:
            title = item.find("div", class_="first-child-description").get_text(
                strip=True
            )
            content = item.find("div", class_="first-child-value").get_text(strip=True)
            dic[title] = content

        # 招聘要求
        driver.get(job["url"] + "/zhaopinyaoqiu")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.chart-small")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # chart-small
        chart_small = soup.find("div", class_="chart-small")
        # display-chart-s
        display_chart_s = chart_small.find_all("div", class_="display-chart-s")
        for item in display_chart_s:
            title = item.find("h4", class_="display-chart-title").get_text(strip=True)
            content = item.find("div", class_="summary").get_text(strip=True)
            dic[title] = content

        # 薪资待遇
        driver.get(job["url"] + "/xinchoudaiyu")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#__nuxt > div > div > div.main > div.position-page > div.detail-content > div.detail-center > div.nuxt-page > div > section:nth-child(2) > div.region-salary > div > div.chart-section-content > div > div > div.chartMain > div.regionLineDesc > div")))
        time.sleep(0.5)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # regionLineChart
        regionLineChart = soup.find("div", class_="region-line-chart")
        # regionLineDescItem
        regionLineDescItem = regionLineChart.find("div", class_="regionLineDescItem")

        descTitle = regionLineDescItem.find("div", class_="descTitle").get_text()
        descNum = regionLineDescItem.find("div", class_="descNum").get_text()
        dic[descTitle] = descNum

        # region-salary
        d = {}
        range_salary = soup.find("div", class_="range-salary")
        regionLineDescItem = range_salary.find("div", class_="regionLineDescItem")
        descTitle = regionLineDescItem.find_all("div", class_="descTitle")
        descNum = regionLineDescItem.find_all("div", class_="descNum")
        for t, n in zip(descTitle, descNum):
            d[t.get_text()] = n.get_text(separator=" ")
        dic["薪资区间变化"] = d

        # regionBarDesc
        regionBarDesc = soup.find("div", class_="regionBarDesc")
        regionBarDescItem = regionBarDesc.find("div", class_="regionBarDescItem")
        descTitle = regionBarDescItem.find("div", class_="descTitle").get_text()
        descNum = regionBarDescItem.find("div", class_="descNum").get_text()
        dic[descTitle] = descNum

        # work-salary
        work_salary = soup.find_all("div", class_="work-salary")
        for item in work_salary:
            # regionLineDescItem
            regionLineDescItem = item.find("div", class_="regionLineDescItem")
            descTitle = regionLineDescItem.find("div", class_="descTitle").get_text()
            descNum = regionLineDescItem.find("div", class_="descNum").get_text()
            dic[descTitle] = descNum

        with open("../output.jl", "a", encoding="utf-8") as f:
            f.write(json.dumps(dic, ensure_ascii=False) + "\n")

        with open("../crawled_urls.txt", "a", encoding="utf-8") as f:
            f.write(job["url"] + "\n")

    except Exception as e:
        # raise e
        print(job)
        print(e)
        return

    driver.quit()

with open(r"C:\Users\Administrator\Desktop\careers\yl1001\jobs.jl", "r", encoding="utf-8") as f:
    jobs = [json.loads(line) for line in f]

if os.path.exists("../crawled_urls.txt"):
    with open("../crawled_urls.txt", "r", encoding="utf-8") as f:
        crawled_urls = list(line.strip() for line in f.readlines())
else:
    crawled_urls = list()

jobs_todo = [job for job in jobs if job["url"] not in crawled_urls]


with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
    results = list(tqdm(
        executor.map(visit_urls, jobs_todo),
        total=len(jobs_todo),
        desc="Processing URLs"
    ))
