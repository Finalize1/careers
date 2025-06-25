import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from tqdm import tqdm


def safe_find_text(element, selector, **kwargs):
    """安全提取文本，找不到时返回空字符串"""
    if element is None:
        return ""
    found = element.find(selector, **kwargs)
    return found.text.strip() if found else ""


def safe_find_all_text(element, selector, **kwargs):
    """安全提取多个元素的文本，找不到时返回空字符串"""
    if element is None:
        return ""
    items = element.find_all(selector, **kwargs)
    return "\n".join([item.text.strip() for item in items]) if items else ""


with open("jobs.txt", "r", encoding="utf-8") as f:
    jobs = f.read()

if os.path.exists("output.jl"):
    os.remove("output.jl")

if os.path.exists("error.txt"):
    os.remove("error.txt")


for job in tqdm(jobs.split("\n")):
    while True:
        try:
            # 打开https://www.zhipin.com/baike/https://www.zhipin.com/baike/
            driver = webdriver.Edge()
            driver.get("https://www.zhipin.com/baike/")

            # 找到<input type="text" placeholder="请输入职位名称" value="" data-v-9504079e="">
            input_element = driver.find_element(
                By.XPATH,
                '//*[@id="content"]/div/div[1]/div/input',
            )
            input_element.send_keys(job)
            input_element.click()

            # 等待下拉菜单出现并点击Python选项
            python_option = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "(//li[contains(@ka, 'positionpedia_position_classification_[')])[1]",
                    )
                )
            )
            python_option.click()  # 即使没有<a>标签也可以点击

            # 切换到新的标签页
            driver.switch_to.window(driver.window_handles[-1])  # 切换到新标签页

            time.sleep(1)  # 等待1秒，让页面加载完成
            # 获取当前页面的HTML内容
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            # 初始化默认值
            wiki_info_box = soup.find("div", class_="wikiInfo-box") or {}
            title = safe_find_text(wiki_info_box, "h1")
            description = safe_find_text(wiki_info_box, "div", class_="describe")

            # 处理可能不存在的列表
            contents = (
                wiki_info_box.find_all("div", class_="list-wrap-item")
                if wiki_info_box
                else []
            )
            content = "\n".join([c.text.strip() for c in contents]) if contents else ""

            sec_body = soup.find_all("div", class_="sec-body") or []
            month = year = skills = delineation = how_list = development_list = (
                interview_list
            ) = ""

            if len(sec_body) > 0:
                month_list = sec_body[0].find("ul", class_="month-list")
                month = safe_find_all_text(month_list, "li")

                year_list = sec_body[0].find(
                    "ul", class_="yaer-list"
                )  # 注意拼写: year-list?
                year = safe_find_all_text(year_list, "li")

            if len(sec_body) > 1:
                skills_list = sec_body[1].find("ul", class_="skills-list")
                skills = safe_find_all_text(skills_list, "li")

                list_wrap = sec_body[1].find(
                    "div", class_="part-show-list-wrap divide-class-list"
                )
                if list_wrap:
                    delineations = []
                    for item in list_wrap.find_all("li"):
                        p_tags = item.find_all("p")
                        (
                            delineations.append(
                                ": ".join([p.text.strip() for p in p_tags])
                            )
                            if p_tags
                            else ""
                        )
                    delineation = "\n".join(delineations) if delineations else ""

                how = sec_body[1].find("div", class_="part-show-list-wrap content-list")
                if how:
                    how_items = []
                    for item in how.find_all("li"):
                        question = safe_find_text(item, "a")
                        p_tag = item.find("p")
                        if p_tag:
                            for div in p_tag.find_all("div"):
                                div.decompose()
                            answer = p_tag.get_text(strip=True)
                            how_items.append(f"{question}\n{answer}\n")
                    how_list = "\n".join(how_items) if how_items else ""

            if len(sec_body) > 2:
                developments = sec_body[2].find_all(
                    "p", class_="question-title-content"
                )
                development_list = (
                    "\n".join([d.text.strip() for d in developments])
                    if developments
                    else ""
                )

            if len(sec_body) > 3:
                interviews = sec_body[3].find_all("p", class_="question-title-content")
                interview_list = (
                    "\n".join([i.text.strip() for i in interviews])
                    if interviews
                    else ""
                )

            # 构建字典（自动跳过空值）
            result = {
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

            # 输出结果（过滤空值）
            cleaned_result = {
                k: v
                for k, v in result.items()
                if v not in ("", None, {}, [])
                and not (isinstance(v, dict) and not any(v.values()))
            }

            with open("output.jl", "a", encoding="utf-8") as f:
                json.dump(cleaned_result, f, ensure_ascii=False)
                f.write("\n")

            driver.quit()  # 关闭浏览器
            break  # 跳出循环
        except Exception as e:
            if "no such element" in str(e):
                input("请手动输入验证码并回车继续...")
                continue
            else:
                # raise e
                with open("error.txt", "a", encoding="utf-8") as f:
                    f.write(job)
                    f.write(": ")
                    f.write(str(e))
                    f.write("\n")
                driver.quit()  # 关闭浏览器
                break  # 跳出循环
