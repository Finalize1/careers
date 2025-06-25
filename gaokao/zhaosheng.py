import pandas as pd
import requests

ssdmList = [
    {
        "text": "北京",
        "value": "11"
    },
    {
        "text": "天津",
        "value": "12"
    },
    {
        "text": "河北",
        "value": "13"
    },
    {
        "text": "山西",
        "value": "14"
    },
    {
        "text": "内蒙古",
        "value": "15"
    },
    {
        "text": "辽宁",
        "value": "21"
    },
    {
        "text": "吉林",
        "value": "22"
    },
    {
        "text": "黑龙江",
        "value": "23"
    },
    {
        "text": "上海",
        "value": "31"
    },
    {
        "text": "江苏",
        "value": "32"
    },
    {
        "text": "浙江",
        "value": "33"
    },
    {
        "text": "安徽",
        "value": "34"
    },
    {
        "text": "福建",
        "value": "35"
    },
    {
        "text": "江西",
        "value": "36"
    },
    {
        "text": "山东",
        "value": "37"
    },
    {
        "text": "河南",
        "value": "41"
    },
    {
        "text": "湖北",
        "value": "42"
    },
    {
        "text": "湖南",
        "value": "43"
    },
    {
        "text": "广东",
        "value": "44"
    },
    {
        "text": "广西",
        "value": "45"
    },
    {
        "text": "海南",
        "value": "46"
    },
    {
        "text": "重庆",
        "value": "50"
    },
    {
        "text": "四川",
        "value": "51"
    },
    {
        "text": "贵州",
        "value": "52"
    },
    {
        "text": "云南",
        "value": "53"
    },
    {
        "text": "西藏",
        "value": "54"
    },
    {
        "text": "陕西",
        "value": "61"
    },
    {
        "text": "甘肃",
        "value": "62"
    },
    {
        "text": "青海",
        "value": "63"
    },
    {
        "text": "宁夏",
        "value": "64"
    },
    {
        "text": "新疆",
        "value": "65"
    }
]

universities=[]

for area in ssdmList:
    print(area)

    url = 'https://gaokao.chsi.com.cn/wap/gdwz/sch'
    data = {
        'yxmc': '',  # 学校名称
        'ssdm': area['value'],  # 省份代码（修改为需要的代码）
        'yxls': '',  # 院校类型
        'xlcc': '',  # 学历层次
        'yxjbz': '',  # 院校级别
        'start': '0',  # 起始位置
        'curPage': '0',  # 当前页（修改为需要的页数）
        'pageSize': '0',  # 每页数据量
        'totalCount': '2886'  # 数据总数
    }

    response = requests.post(url, data=data)
    data = response.json()

    pages = data["msg"]["totalCount"] // data["msg"]["pageCount"]
    for i in range(pages + 1):
        url = 'https://gaokao.chsi.com.cn/wap/gdwz/sch'
        data = {
            'yxmc': '',  # 学校名称
            'ssdm': area['value'],  # 省份代码（修改为需要的代码）
            'yxls': '',  # 院校类型
            'xlcc': '',  # 学历层次
            'yxjbz': '',  # 院校级别
            'start': i * 20,  # 起始位置
            'curPage': '0',  # 当前页（修改为需要的页数）
            'pageSize': '0',  # 每页数据量
            'totalCount': '2886'  # 数据总数
        }
        response = requests.post(url, data=data)
        d = response.json()
        for university in d["msg"]["list"]:
            dic={}
            dic["所在地"]=area["text"]
            dic["大学"]=university["orgName"]
            dic["学校网址"]=university["xxwz"]
            dic["招生网址"]=university["zswz"]
            dic["咨询电话"]=university["dh"]
            universities.append(dic)

# 转换成 DataFrame
df = pd.DataFrame(universities)
df.to_excel("高考.xlsx", index=False)
