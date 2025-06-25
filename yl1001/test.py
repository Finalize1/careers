import os
import time
import json

import brotli
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
    urls = [
        job["url"],
        job["url"] + "/zhaopinyaoqiu",
        job["url"] + "/xinchoudaiyu"
    ]
    driver = webdriver.Edge()
    driver.get("https://daquan.yl1001.com")
    # 这里可加载 cookies
    load_cookies(driver, "cookies.json")
    driver.refresh()

    dic = {}

    dic["职业类别"] = job["类别"]
    dic["职业名称"] = job["职业名称"]
    dic["职业描述"] = job["职业描述"]
    dic["url"] = job["url"]

    for idx, url in enumerate(urls,start=1):
        driver.refresh()
        driver.get(url)
        # 输出请求头headers
        l=[]
        print(f"请求 {url} 的 headers:")
        for request in driver.requests:
            if request.url == url:
                print(request.headers)
                break
        # 使用requests库访问url




        # 刷新页面
        wait = WebDriverWait(driver, 10)
        for request in driver.requests:
            if request.response and request.url == "https://daquan.yl1001.com/api-ce/front/career/position/data":
                response_body = request.response.body
                if request.response.headers.get('Content-Encoding') == 'br':
                    try:
                        decompressed = brotli.decompress(response_body)
                        data = json.loads(decompressed.decode('utf-8'))
                        if idx == 1:
                            dic["职业定义"] = data["data"][0]["children"][0]["data"]["answer"]["answerContent"]
                            dic["主要工作任务"] = '\n'.join(
                                [entry["layerValue"] for entry in data["data"][0]["children"][1]["data"]])
                            dic["工作场所"] = data["data"][1]["children"][0]["data"][0]["layerValue"]
                            dic["职业风险"] = {entry["description"]: entry["layerValue"] for entry in
                                               data["data"][1]["children"][1]["data"]}
                            dic["工作环境"] = {entry["description"]: entry["layerValue"] for entry in
                                               data["data"][1]["children"][2]["data"]}
                            dic.update({entry["description"]: entry["layerValue"] for entry in
                                        data["data"][1]["children"][3]["data"]})
                            dic.update({entry["description"]: entry["layerValue"] for entry in
                                        data["data"][1]["children"][4]["data"]})
                            print(dic)
                        elif idx == 2:
                            print(data["data"][0]["children"][1]["data"])
                            dic["专业能力要求"] = {entry["description"]: entry["layerValue"] for entry in
                                                   data["data"][0]["children"][0]["data"]}
                            dic["通用素质要求"] = {entry["description"]: entry["layerValue"] for entry in
                                                   data["data"][0]["children"][1]["data"]}
                            dic["性格要求"] = {entry["description"]: entry["layerValue"] for entry in
                                               data["data"][0]["children"][2]["data"]}
                            dic["知识要求"] = {entry["description"]: entry["layerValue"] for entry in
                                                data["data"][0]["children"][3]["data"]}
                            print(dic)
                        elif idx == 3:
                            soup = BeautifulSoup(driver.page_source, "html.parser")

                            regionLineChart = soup.find("div", class_="regionLineChart")
                            regionLineDescItem = regionLineChart.find("div", class_="regionLineDescItem")
                            descTitle = regionLineDescItem.find("div", class_="descTitle").get_text()
                            descNum = regionLineDescItem.find("div", class_="descNum").get_text()
                            dic[descTitle] = descNum

                            d = {}
                            range_salary = soup.find("div", class_="range-salary")
                            regionLineDescItem = range_salary.find("div", class_="regionLineDescItem")
                            descTitle = regionLineDescItem.find_all("div", class_="descTitle")
                            descNum = regionLineDescItem.find_all("div", class_="descNum")
                            for t, n in zip(descTitle, descNum):
                                d[t.get_text()] = n.get_text(separator=" ")
                            dic["薪资区间变化"] = d

                            regionBarDesc = soup.find("div", class_="regionBarDesc")
                            regionBarDescItem = regionBarDesc.find("div", class_="regionBarDescItem")
                            descTitle = regionBarDescItem.find("div", class_="descTitle").get_text()
                            descNum = regionBarDescItem.find("div", class_="descNum").get_text()
                            dic[descTitle] = descNum

                            work_salary = soup.find_all("div", class_="work-salary")
                            for item in work_salary:
                                regionLineDescItem = item.find("div", class_="regionLineDescItem")
                                descTitle = regionLineDescItem.find("div", class_="descTitle").get_text()
                                descNum = regionLineDescItem.find("div", class_="descNum").get_text()
                                dic[descTitle] = descNum

                    except Exception as e:
                        print("解压或解析失败:", e)
                        raise e
                else:
                    print("响应未压缩或使用其他压缩方式")

    print(dic)

    driver.quit()


with open("jobs.jl", "r", encoding="utf-8") as f:
    jobs = [json.loads(line) for line in f]

with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
    executor.map(visit_urls, jobs)
#
# import json
#
# dic = {}
#
# with open("102.json", "r", encoding="utf-8") as f:
#     data = json.load(f)
#
# dic["职业定义"] = data["data"][0]["children"][0]["data"]["answer"]["answerContent"]
# dic["主要工作任务"] = '\n'.join([entry["layerValue"] for entry in data["data"][0]["children"][1]["data"]])
# dic["工作场所"] = data["data"][1]["children"][0]["data"][0]["layerValue"]
# dic["职业风险"] = {entry["description"]: entry["layerValue"] for entry in data["data"][1]["children"][1]["data"]}
# dic["工作环境"] = {entry["description"]: entry["layerValue"] for entry in data["data"][1]["children"][2]["data"]}
# dic.update({entry["description"]: entry["layerValue"] for entry in data["data"][1]["children"][3]["data"]})
# dic.update({entry["description"]: entry["layerValue"] for entry in data["data"][1]["children"][4]["data"]})
#
# with open("103.json", "r", encoding="utf-8") as f:
#     data = json.load(f)
#
# dic["专业能力要求"] = {entry["description"]: entry["layerValue"] for entry in data["data"][0]["children"][0]["data"]}
# dic["通用素质要求"] = {entry["description"]: entry["layerValue"] for entry in data["data"][0]["children"][1]["data"]}
# dic["性格要求"] = {entry["description"]: entry["layerValue"] for entry in data["data"][0]["children"][2]["data"]}
# dic["知识要求"] = {entry["description"]: entry["layerValue"] for entry in data["data"][0]["children"][3]["data"]}
#
# print(dic)
