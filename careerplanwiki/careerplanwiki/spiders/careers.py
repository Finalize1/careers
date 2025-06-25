import scrapy
import json
from bs4 import BeautifulSoup


class CareerSpider(scrapy.Spider):
    name = "careerplanwiki"
    allowed_domains = ["careerplanwiki.com"]  # 替换为实际域名
    start_urls = ["https://www.careerplanwiki.com/position"]  # 替换为实际URL

    def start_requests(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://www.careerplanwiki.com/position",
        }
        for url in self.start_urls:
            yield scrapy.Request(url, headers=headers, callback=self.parse)

    def parse(self, response):
        # 遍历每个分类区块
        for category in response.css("div.m-item-tt"):
            category_name = category.css("span::text").get()

            # 获取相邻的职位列表区块
            item_list = category.xpath(
                './following-sibling::div[contains(@class,"m-item-list")][1]'
            )

            # 提取该分类下的所有职位
            for job in item_list.css("li"):
                # 如果需要跟进职位详情页
                detail_url = job.css("a::attr(href)").get()
                yield response.follow(
                    detail_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
                        "Referer": response.url,
                    },
                    callback=self.parse_detail,
                    meta={
                        "category": category_name,
                        "job_name": job.css("a::text").get(),
                    },
                )

    def parse_detail(self, response):
        # 提取详细信息
        soup = BeautifulSoup(response.text, "html.parser")
        # 找到class="container detail-content"
        container = soup.find("div", class_="container detail-content")
        title = [t.text for t in container.find_all("h2")]
        suffixes = ["\n" + t for t in title[1:]]

        # 2. 提取每个标题对应的内容
        content_dict = {}
        current_title = None

        for element in container.find_all(["h2", "div", "ul"]):
            if element.name == "h2":
                current_title = element.get_text(strip=True)
                content_dict[current_title] = []
            elif current_title:  # 只记录在标题后的内容
                # 提取当前元素的纯文本（去除HTML标签）
                text = element.get_text(" ", strip=True)
                if text:  # 忽略空内容
                    content_dict[current_title].append(text)

        # 3. 合并每个标题下的内容为字符串
        for title in content_dict:
            content_dict[title] = "\n".join(content_dict[title])

        item = {
            "类别": response.meta["category"],
            "职业名": response.meta.get("job_name"),
            "url": response.url,
        }

        # 输出结果
        for title, content in content_dict.items():
            for suffix in suffixes:
                if content.endswith(suffix):
                    content = content[: -len(suffix)]
                    break
            item[title] = content

        yield item
