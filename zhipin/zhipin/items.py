# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ZhipinItem(scrapy.Item):
    category = scrapy.Field()
    job_name = scrapy.Field()
    job_url = scrapy.Field()
    pass
