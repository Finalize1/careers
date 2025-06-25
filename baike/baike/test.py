import json
import selenium
from selenium import webdriver
import time
import os
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from tqdm import tqdm


def save_cookies(driver, filename):
    """保存 Cookies（包含 domain/path）"""
    cookies = driver.get_cookies()
    with open(filename, "w") as f:
        json.dump(cookies, f)  # 保存完整 Cookies 信息


def load_cookies(driver, filename):
    """加载 Cookies（确保 domain/path 正确）"""
    with open(filename, "r") as f:
        cookies = json.load(f)
    driver.get("https://baike.51job.com/zhiwei/all/")  # 先访问根域名
    for cookie in cookies:
        # 确保 Cookies 能作用于所有子页面
        if "domain" not in cookie:
            cookie["domain"] = ".51job.com"  # 通配符域名
        driver.add_cookie(cookie)


# job_list = []
# # 查找第一个<p class="s_jname">后端开发</p>以及它后面第一个<div class="lts">
# f_list = driver.find_elements(By.CSS_SELECTOR, "div.f_list")
# # 查找<p class="s_jname">
# s_jname = driver.find_elements(By.CSS_SELECTOR, "p.s_jname")
# # 查找<div class="lts">
# lts = driver.find_elements(By.CSS_SELECTOR, "div.lts")[1:]
# # 遍历所有职位类别链接
# for i in range(len(s_jname)):
#     # 获取职位类别名称
#     job_category = s_jname[i].text
#     # 获取职位类别链接
#     job_links = lts[i].find_elements(By.CSS_SELECTOR, "a")
#     # 遍历所有职位链接
#     for job_link in job_links:
#         job_name = job_link.text
#         job_url = job_link.get_attribute("href")
#         job_list.append([job_category, job_name, job_url])
#         print(job_category, job_name, job_url)


# # 初始化浏览器
# driver = webdriver.Edge()
# driver.get("https://baike.51job.com/zhiwei/all/")

# # 手动登录
# input("请手动登录，完成后按回车继续...")

# # 保存 Cookies
# save_cookies(driver, "cookies.json")
# driver.quit()


with open("jobs.txt", "r", encoding="utf-8") as f:
    job_list = [line.strip() for line in f.readlines()]

# 重新启动并加载 Cookies
options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
driver = webdriver.Edge(options=options)

# if os.path.exists("jobs.jl"):
#     os.remove("jobs.jl")

load_cookies(driver, "cookies.json")
driver.refresh()

driver.get("https://baike.51job.com/zhiwei/all/")

# 显式等待页面加载
wait = WebDriverWait(driver, 10)

if os.path.exists("crawled_urls.txt"):
    with open("crawled_urls.txt", "r", encoding="utf-8") as f:
        crawled_urls = list(line.strip() for line in f.readlines())
else:
    crawled_urls = list()

# 遍历职位列表
for job_url in tqdm(job_list):
    if job_url in crawled_urls:
        continue

    dic = {}

    try:
        driver.get(job_url)
        # 等待页面加载完成
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.nav-tab")))
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # <div class="nav-tab" data-v-8172b960=""><a href="/zhiwei/01241/" class="nuxt-link-exact-active nuxt-link-active tab-item active" data-v-8172b960="" aria-current="page"><span data-v-8172b960="">岗位职责</span></a><a href="/zhiwei/01241/xinzi/" class="tab-item" data-v-8172b960=""><span data-v-8172b960="">工资薪酬</span></a><a href="/zhiwei/01241/trends/" class="tab-item" data-v-8172b960=""><span data-v-8172b960="">就业前景</span></a></div>
        # href="/zhiwei/01241/xinzi/"
        xinzi = soup.find("div", class_="nav-tab").find(
            "a", href=re.compile(r"/zhiwei/\d+/xinzi/")
        )

        dic["url"] = job_url

        top_title = soup.find("div", class_="top-title ellipsis")
        base_job_name = top_title.get_text(strip=True) if top_title else ""
        dic["职位名称"] = base_job_name

        intro_info = soup.find("div", class_="intro-info")
        description = intro_info.get_text(strip=True) if intro_info else ""
        dic["职位简介"] = description

        job_elements = driver.find_elements(By.CSS_SELECTOR, "div.job")
        # 遍历每个职位元素
        d = {}
        for job_element in job_elements:
            job_name = job_element.text.strip()
            if job_name:  # 检查职位名称是否匹配
                job_element.click()  # 点击匹配的职位
                soup = BeautifulSoup(driver.page_source, "html.parser")
                # 获取panel panel-1
                panel_1 = soup.find("div", class_="panel panel-1")

                # 找info-item degree，info-item major，info-item major-skill，info-item other-skill
                degree = panel_1.find("div", class_="info-item degree")
                major = panel_1.find("div", class_="info-item major")
                major_skill = panel_1.find("div", class_="info-item major-skill")
                other_skill = panel_1.find("div", class_="info-item other-skill")

                degree = degree.find("div", class_="rgt-content") if degree else ""
                major = major.find("div", class_="rgt-content") if major else ""
                major_skill = (
                    major_skill.find("div", class_="rgt-content") if major_skill else ""
                )
                other_skill = (
                    other_skill.find("div", class_="rgt-content") if other_skill else ""
                )

                major_skill_label = (
                    major_skill.find("div", class_="skill-it-label")
                    if major_skill
                    else ""
                )
                if major_skill_label:
                    major_skill_label = major_skill_label.get_text(
                        strip=True, separator=","
                    ).split(",")

                # 找到 skill-it-precent 的style
                major_skill_precent = (
                    major_skill.find("div", class_="skill-it-precent")
                    if major_skill
                    else ""
                )
                if major_skill_precent:
                    li = []
                    lv = major_skill_precent.find_all("div", class_="lv")
                    precent = []
                    if lv:
                        for l in lv:
                            precent.append(l.find("span").get_text(strip=True))
                        precent_dict = {
                            str((i + 1) * 100 // len(precent)): precent[i]
                            for i in range(len(precent))
                        }

                    pro_outs = major_skill_precent.find_all("div", class_="pro-out")
                    # 遍历每个 "pro-out" 元素
                    for pro_out in pro_outs:
                        # 查找其中的 "pro-inner" 元素
                        pro_inner = pro_out.find("div", class_="pro-inner")
                        # 获取 "pro-inner" 元素的 style 属性
                        style = pro_inner.get("style")
                        # 提取宽度值（纯数字）
                        width = str(re.search(r"width:\s*(\d+)%", style).group(1))
                        li.append(precent_dict[width])  # 输出宽度值

                degree_text = degree.get_text(strip=True) if degree else ""
                major_text = major.get_text(strip=True) if major else ""
                major_skill_text = {label: i for label in major_skill_label for i in li}

                other_skill_text = (
                    other_skill.get_text(strip=True) if other_skill else ""
                )

                d[job_name] = {
                    "学历要求": degree_text,
                    "专业要求": major_text,
                    "专业技能": major_skill_text,
                    "其他技能": other_skill_text,
                }
        dic["岗位要求"] = d

        # info-item job-content
        info_item = driver.find_elements(By.CSS_SELECTOR, "div.y-it")
        for item in info_item:
            # 找info-item job-content
            job_content = item.text.strip()
            if job_content:
                item.click()  # 点击匹配的职位
                soup = BeautifulSoup(driver.page_source, "html.parser")
                # content
                content = soup.find("div", class_="content").find("p")
                dic[item.text.strip()] = content.get_text(strip=True) if content else ""

    except Exception as e:
        # raise
        print(f"点击职位失败: {e}")
        print(job_url)
        continue

    if xinzi:
        try:
            driver.get(job_url + "xinzi/")
            # 等待页面加载完成
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.salary-sum"))
            )
            soup = BeautifulSoup(driver.page_source, "html.parser")
            # salary-sum
            salary_sum = soup.find("div", class_="salary-sum")
            salary_sum_p = salary_sum.find_all("p")
            dic["平均月薪"] = (
                salary_sum_p[0].get_text(strip=True).split(":")[1].strip()
                if salary_sum_p
                else ""
            )
            dic["市场估值"] = (
                salary_sum_p[1].get_text(strip=True).split(":")[1].strip()
                if salary_sum_p
                else ""
            )

            # echart-image pie-echart
            echart_image = soup.find("div", class_="echart-image pie-echart")
            desc = echart_image.find("div", class_="desc")
            dic["年收入分布"] = desc.get_text(strip=True) if desc else ""

        except Exception as e:
            # raise
            print(f"点击薪资失败: {e}")
            print(job_url + "xinzi/")
            continue

    with open("jobs.jl", "a", encoding="utf-8") as f:
        f.write(json.dumps(dic, ensure_ascii=False) + "\n")
    with open("crawled_urls.txt", "a", encoding="utf-8") as f:
        f.write(job_url + "\n")

driver.quit()
