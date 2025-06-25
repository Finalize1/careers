import scrapy
import json
import os
from bs4 import BeautifulSoup


class CareerSpider(scrapy.Spider):
    name = "baike"
    allowed_domains = ["51job.com"]
    start_urls = ["https://baike.51job.com/zhiwei/all/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.first_item = True
        if os.path.exists("output.jl"):
            os.remove("output.jl")

    def start_requests(self):
        # 读取cookies.txt文件
        with open("cookies.txt", "r") as f:
            cookies = f.read().strip()
            cookies = cookies.split("\n")
            cookies = {cookie.split("=")[0]: cookie.split("=")[1] for cookie in cookies}

        # 访问需要登录的页面
        yield scrapy.Request(
            "https://www.51job.com/",
            cookies=cookies,
            callback=self.parse_account,
        )

    def parse_account(self, response):
        yield scrapy.Request(
            "https://www.51job.com/",
            cookies=response.request.cookies,
            callback=self.parse_account,
            dont_filter=True,  # 允许重复请求
        )
        # 查找<li class="tle"><a class="uname e_icon at" id="pc_uname" href="https://we.51job.com/pc/my/myjob?lang=c">？？？</a></li>
        soup = BeautifulSoup(response.text, "html.parser")
        li = soup.find("li", class_="tle")
        print(li)
        if li:
            a = li.find("a", class_="uname e_icon at")
            if a:
                self.logger.info(f"登录成功，当前用户: {a.text}")
            else:
                self.logger.error("未找到用户名")

    def parse(self, response):
        self.logger.info(f"开始解析主页面: {response.url}")
        # 使用CSS选择器提取所有类别和职位
        categories = response.css("div.f_list")

        for category in categories:
            # 提取类别名称
            category_name = category.css("p.s_jname::text").get()
            if not category_name:
                continue

            # 提取该类别下的所有职位
            jobs = category.css("div.lts a")
            for job in jobs:
                yield scrapy.Request(
                    url=response.urljoin(job.css("::attr(href)").get()),
                    callback=self.parse_job_detail,
                    meta={
                        "category": category_name.strip(),
                        "job_name": job.css("::attr(title)").get(),
                    },
                )

    def parse_job_detail(self, response):
        # 解析职位详情页
        yield {
            "category": response.meta["category"],
            "job_name": response.meta["job_name"],
            "job_description": response.css("div.job-detail::text").getall(),
            "job_requirements": response.css("div.job-requirements::text").getall(),
            "salary_range": response.css("span.salary::text").get(),
            "experience_required": response.css("span.experience::text").get(),
            "education_required": response.css("span.education::text").get(),
            "job_url": response.url,
        }
