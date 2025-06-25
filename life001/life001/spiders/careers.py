import scrapy
import json
import os
from bs4 import BeautifulSoup


class CareerSpider(scrapy.Spider):
    name = "life001"
    allowed_domains = ["life001.com"]
    start_urls = ["https://www.life001.com/career"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.first_item = True
        if os.path.exists("output.jl"):
            os.remove("output.jl")

    def start_requests(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://www.life001.com/career",
        }
        for url in self.start_urls:
            yield scrapy.Request(url, headers=headers, callback=self.parse)

    def parse(self, response):
        self.logger.info(f"开始解析主页面: {response.url}")
        more_links = response.css("li.chip-link a::attr(href)").getall()

        if not more_links:
            self.logger.warning("未找到'more'链接")
            return

        for link in more_links:  # 处理所有more链接，不只是最后一个
            yield response.follow(link, callback=self.parse_more)

    def parse_more(self, response):
        self.logger.info(f"解析更多页面: {response.url}")
        job_links = response.css("li.truncate a::attr(href)").getall()

        if not job_links:
            self.logger.warning(f"页面 {response.url} 未找到职位链接")
            return

        for link in job_links:
            yield response.follow(link, callback=self.parse_job)

    def parse_job(self, response):
        self.logger.info(f"解析职位页面: {response.url}")
        category = response.css("ul.text li a::text").get(default="").strip()
        job_name = (
            response.css("h1::text").get(default="").strip()
        )  # 假设职位名在h1标签

        if not category or not job_name:
            self.logger.warning(f"无法从 {response.url} 提取分类或职位名")
            return

        more_job_links = response.css("li.p-3 a::attr(href)").getall()

        if not more_job_links:
            self.logger.warning(f"职位 {job_name} 没有详情链接")
            return

        for link in more_job_links:
            yield response.follow(
                link,
                callback=self.parse_job_details,
                meta={"category": category, "job_name": job_name},
                dont_filter=True,
            )

    def parse_job_details(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        h1_tag = soup.find("h1", class_="text-heading")
        div_tag = soup.find("div", class_="mrender content-blog")

        h1_text = h1_tag.get_text(strip=True) if h1_tag else ""
        div_text = div_tag.get_text(strip=True) if div_tag else ""

        yield {
            "category": response.meta["category"],
            "job_name": response.meta["job_name"],
            "title": h1_text,
            "content": div_text,
            "holland": div_text if "霍兰德" in h1_text else "",
            "status": div_text if "就业现状、趋势展望与成长路径" in h1_text else "",
            "url": response.url,
        }

    def closed(self, output_file):
        def merge_dicts_high_performance(dicts):
            result = {}
            for d in dicts:
                for k, v in d.items():
                    if v:  # 只处理非空值
                        result[k] = v
                    elif k not in result:  # 如果键不存在，设为空字符串
                        result[k] = ""
            return result

        with open("output.jl", "r", encoding="utf-8") as f:
            data = [json.loads(line) for line in f]
            # 按job_name分组
            grouped_data = {}
            for d in data:
                job_name = d.get("job_name")
                if job_name:
                    if job_name not in grouped_data:
                        grouped_data[job_name] = []
                    grouped_data[job_name].append(d)

        with open("merged_output.json", "w", encoding="utf-8") as f:
            merged = [merge_dicts_high_performance(v) for _, v in grouped_data.items()]
            json.dump(merged, f, ensure_ascii=False, indent=4)
