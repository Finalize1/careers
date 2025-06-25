import time

import scrapy
import json
import os
from bs4 import BeautifulSoup


class CareerSpider(scrapy.Spider):
    name = "yl1001"
    allowed_domains = ["yl1001.com"]
    start_urls = ["https://daquan.yl1001.com/zhiye"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.first_item = True
        # if os.path.exists("output.jl"):
        #     os.remove("output.jl")

    def start_requests(self):
        with open(r"C:\Users\Administrator\Desktop\careers\yl1001\jobs.jl", "r", encoding="utf-8") as f:
            jobs = [json.loads(line) for line in f if line.strip()]

        for job in jobs:
            id = str(job["url"].split("/")[-1])

            headers = {
                "Cookie": "sl-session=ktlzDGrwQGiTodGGL6gjWg==; token=eyJhbGciOiJIUzI1NiJ9.eyJib2R5Ijoie1widGlja2V0XCI6XCJvZ216d1g3WHJaZklvZHREXCIsXCJwZXJzb25JZFwiOjI1MDc3ODQ5fSIsImV4cCI6MTc0OTA5NTQ1NH0.5xUEf-RZpbU2QibYTFPtILLhh8dY7iNSWZOnJY2Hme8; Hm_lvt_2ef0be57bbce53c0182f459b405dcc12=1748912972,1748921078,1748999928,1749016017; HMACCOUNT=7954AD50A8C14F69; sl-challenge-server=cloud; sl_jwt_session=EwnxYt4IQGjcMspTDVH+KQ==; sl_jwt_sign=; Hm_lpvt_2ef0be57bbce53c0182f459b405dcc12=1749024350",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
            }

            yield scrapy.Request(
                url="https://daquan.yl1001.com/api-ce/front/career/position/data",
                method="POST",
                headers=headers,
                body=json.dumps({"id": id, "layerIds": "61_8", "topId": "1"}),
                callback=self.parse_job,
                meta={"job": job},
            )

    def parse_job(self, response):
        print(response)




if "__main__" == __name__:
    from scrapy.crawler import CrawlerProcess
    process = CrawlerProcess(settings={
        "FEEDS": {
            "yl1001/output.jl": {
                "format": "jsonlines",
                "overwrite": True,
            },
        },
        "LOG_LEVEL": "INFO",
    })
    process.crawl(CareerSpider)
    process.start()

