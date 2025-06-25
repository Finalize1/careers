import json
import scrapy
from scrapy_playwright.page import PageMethod
from itemadapter import ItemAdapter


class ZhipinSpider(scrapy.Spider):
    name = "zhipin"
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": False,  # 调试时可设为True
            "timeout": 10 * 1000,  # 30秒
        },
        "FEEDS": {
            "output.jl": {
                "format": "jsonlines",
                "encoding": "utf8",
                "store_empty": False,
            }
        },
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    def start_requests(self):
        with open("jobs.txt", "r", encoding="utf-8") as f:
            jobs = [job.strip() for job in f.readlines() if job.strip()]

        for job in jobs:
            yield scrapy.Request(
                url="https://www.zhipin.com/baike/",
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("fill", 'input[placeholder="请输入职位名称"]', job),
                        PageMethod(
                            "click",
                            "(//li[contains(@ka, 'positionpedia_position_classification_[')])[1]",
                        ),
                    ],
                    "playwright_include_page": True,
                    "job": job,  # 传递职位名称
                },
                callback=self.parse_page,
                errback=self.errback,
            )

    async def parse_page(self, response):
        page = response.meta["playwright_page"]
        job = response.meta["job"]

        try:
            # 获取处理后的页面HTML
            html = await page.content()

            # 使用scrapy的Selector代替BeautifulSoup
            wiki_info_box = response.css("div.wikiInfo-box")
            title = wiki_info_box.css("h1::text").get("").strip()
            description = wiki_info_box.css("div.describe::text").get("").strip()

            # 工作内容
            contents = wiki_info_box.css("div.list-wrap-item::text").getall()
            content = "\n".join([c.strip() for c in contents if c.strip()])

            # 各部分数据处理
            sec_bodies = response.css("div.sec-body")
            result = {
                "职位": title,
                "描述": description,
                "工作内容": content if content else None,
            }

            # 月薪和年限
            if len(sec_bodies) > 0:
                month = sec_bodies[0].css("ul.month-list li::text").getall()
                year = sec_bodies[0].css("ul.yaer-list li::text").getall()
                if month:
                    result["月薪环比变化"] = "\n".join([m.strip() for m in month])
                if year:
                    result["工作年限薪酬分布"] = "\n".join([y.strip() for y in year])

            # 入门指南
            if len(sec_bodies) > 1:
                skills = sec_bodies[1].css("ul.skills-list li::text").getall()
                if skills:
                    result.setdefault("入门指南", {})["从业条件"] = "\n".join(
                        [s.strip() for s in skills]
                    )

                # 职业划分
                delineations = []
                for li in sec_bodies[1].css(
                    "div.part-show-list-wrap.divide-class-list li"
                ):
                    question = li.css("p:first-child::text").get("").strip()
                    answer = "".join(li.css("p:last-child::text").getall()).strip()
                    if question or answer:
                        delineations.append(f"{question}: {answer}")
                if delineations:
                    result["入门指南"]["职业划分"] = "\n".join(delineations)

                # 如何入门
                how_items = []
                for li in sec_bodies[1].css("div.part-show-list-wrap.content-list li"):
                    question = li.css("a::text").get("").strip()
                    answer = "".join(li.css("p::text").getall()).strip()
                    if question or answer:
                        how_items.append(f"{question}\n{answer}")
                if how_items:
                    result["入门指南"]["看看其他人如何入门的"] = "\n".join(how_items)

            # 职业成长
            if len(sec_bodies) > 2:
                developments = (
                    sec_bodies[2].css("p.question-title-content::text").getall()
                )
                if developments:
                    result.setdefault("职业成长", {})["职业技能"] = "\n".join(
                        [d.strip() for d in developments]
                    )

            # 求职面试
            if len(sec_bodies) > 3:
                interviews = (
                    sec_bodies[3].css("p.question-title-content::text").getall()
                )
                if interviews:
                    result["求职面试"] = "\n".join([i.strip() for i in interviews])

            # 清理空值
            cleaned_result = {
                k: v
                for k, v in result.items()
                if v not in (None, "", {}, [])
                and not (isinstance(v, dict) and not any(v.values()))
            }

            yield cleaned_result

        except Exception as e:
            self.logger.error(f"Error processing {job}: {str(e)}")
            yield {"职位": job, "error": str(e)}
        finally:
            await page.close()

    async def errback(self, failure):
        page = failure.request.meta["playwright_page"]
        job = failure.request.meta["job"]
        await page.close()

        yield {
            "职位": job,
            "error": str(failure.value),
        }
