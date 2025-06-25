import scrapy


class CareerItem(scrapy.Item):
    category = scrapy.Field()  # 职业分类(如"产品"、"运营")
    job_name = scrapy.Field()  # 职位名称
    job_url = scrapy.Field()  # 职位链接
    job_title = scrapy.Field()  # 职位标题(alt文本)
    # 可以添加更多字段
