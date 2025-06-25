import selenium
from selenium import webdriver
import time


def save_cookies(driver, filename):
    cookies = driver.get_cookies()
    with open(filename, "w") as f:
        for cookie in cookies:
            f.write(f"{cookie['name']}={cookie['value']}\n")


def load_cookies(driver, filename):
    with open(filename, "r") as f:
        for line in f:
            if "=" in line:
                name, value = line.strip().split("=", 1)
                driver.add_cookie({"name": name, "value": value})


# 初始化浏览器
driver = webdriver.Edge()
driver.get("https://www.51job.com/")  # 先访问首页

# 加载cookies前需要先访问一次域名
time.sleep(2)
load_cookies(driver, "cookies.txt")

# 刷新页面使cookies生效
driver.refresh()
time.sleep(2)

# 访问目标页面
driver.get("https://baike.51job.com/zhiwei/01211/")

# 检查登录状态
try:
    account = driver.find_element_by_css_selector("li.tle a.uname")
    print("登录成功，账号:", account.text)
except:
    print("登录失败，请检查cookies是否有效")

input("按回车键退出...")
driver.quit()
