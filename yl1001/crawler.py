import json

import requests
from tqdm import tqdm

with open("jobs.jl", "r", encoding="utf-8") as f:
    jobs = [json.loads(line) for line in f if line.strip()]

with open("crawled_urls.txt", "r", encoding="utf-8") as f:
    crawled_urls = set(line.strip() for line in f if line.strip())


cookies = '''
sl-challenge-server=cloud; Hm_lvt_2ef0be57bbce53c0182f459b405dcc12=1748999928,1749016017,1749033196,1749085554; HMACCOUNT=7954AD50A8C14F69; sl-session=HWJUBH5DQmiB0pNEbjuAYQ==; Hm_lvt_606edec2c11e852dcc37686e8b723098=1749088223; HMACCOUNT=7954AD50A8C14F69; Hm_lpvt_606edec2c11e852dcc37686e8b723098=1749094844; Hm_lvt_0216ff792088201b251e5b7ae8ac7ffb=1749094859; Hm_lpvt_0216ff792088201b251e5b7ae8ac7ffb=1749094925; token=eyJhbGciOiJIUzI1NiJ9.eyJib2R5Ijoie1widGlja2V0XCI6XCJiMGR1SFRsT0RrcmM0b0g1XCIsXCJwZXJzb25JZFwiOjI1MDc3ODQ5fSIsImV4cCI6MTc0OTE4ODE1N30.kRY8C6lgRPCrUD3xfqvnfskAMPjKUpXYgg-DgmkbXsI; sl_jwt_session=0MISFwJJQWjuqwiVvDwXLg==; sl_jwt_sign=; Hm_lpvt_2ef0be57bbce53c0182f459b405dcc12=1749105396
'''.strip()


for job in tqdm(jobs):
    try:
        if job["url"] in crawled_urls:
            continue
        dic = {}

        dic["职业类别"] = job["类别"]
        dic["职业名称"] = job["职业名称"]
        dic["职业描述"] = job["职业描述"]
        dic["url"] = job["url"]

        id = str(job["url"].split("/")[-1])

        headers = {
            "Cookie": cookies,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        }

        url = "https://daquan.yl1001.com/api-ce/front/career/position/data"

        response = requests.post(url, headers=headers, json={"id": id, "layerIds": "61_8", "topId": "1"})
        data = json.loads(response.text)

        dic["职业定义"] = data["data"][0]["children"][0]["data"]["answer"]["answerContent"]
        dic["主要工作任务"] = '\n'.join(
            [entry["layerValue"] for entry in data["data"][0]["children"][1]["data"]])
        dic["工作场所"] = data["data"][1]["children"][0]["data"][0]["layerValue"]
        dic["职业风险"] = '\n'.join([f'{entry["description"]}: {entry["layerValue"]}' for entry in
                           data["data"][1]["children"][1]["data"]])
        dic["工作环境"] = '\n'.join([f'{entry["description"]}: {entry["layerValue"]}' for entry in
                           data["data"][1]["children"][2]["data"]])
        dic.update({entry["description"]: entry["layerValue"] for entry in
                    data["data"][1]["children"][3]["data"]})
        dic.update({entry["description"]: entry["layerValue"] for entry in
                    data["data"][1]["children"][4]["data"]})

        response = requests.post(url, headers=headers, json={"id": id, "layerIds": "15", "topId": "74"})
        data = json.loads(response.text)

        dic["专业能力要求"] = '\n'.join([f'{entry["description"]}: {entry["layerValue"]}' for entry in
                           data["data"][0]["children"][0]["data"]])
        dic["通用素质要求"] = '\n'.join([f'{entry["description"]}: {entry["layerValue"]}' for entry in
                           data["data"][0]["children"][1]["data"]])
        dic["性格要求"] = '\n'.join([f'{entry["description"]}: {entry["layerValue"]}' for entry in
                           data["data"][0]["children"][2]["data"]])
        dic["知识要求"] = '\n'.join([f'{entry["description"]}: {entry["layerValue"]}' for entry in
                           data["data"][0]["children"][3]["data"]])

        response = requests.post("https://daquan.yl1001.com/api-ce/front/career/position/region", headers=headers, json={"id": id})
        data = json.loads(response.text)
        dic["全国平均薪酬"] = f'￥{data["data"]["average"]}/月'

        response = requests.post("https://daquan.yl1001.com/api-ce/front/career/position/section", headers=headers,json={"id": id})
        data = json.loads(response.text)
        dic["占比最多的薪酬区间"] = f'￥{data["data"]["maxRateRange"]} {data["data"]["maxRate"]}%'

        response = requests.post("https://daquan.yl1001.com/api-ce/front/career/position/top", headers=headers,json={"id": id, "beginTime": "2025-05-01", "endTime": "2025-06-01"})
        data = json.loads(response.text)
        dic["全国月收入平均值"] = f'￥{data["data"]["salaryNum"]}'

        response = requests.post("https://daquan.yl1001.com/api-ce/front/career/position/salary/work/year", headers=headers,json={"id": id, "beginTime": "2024-12-01", "endTime": "2025-05-01"})
        data = json.loads(response.text)
        dic.update({entry["expCodeStr"]: f'￥{entry["salaryNum"]}/月' for entry in data["data"]})

        response = requests.post("https://daquan.yl1001.com/api-ce/front/career/position/salary/education", headers=headers,json={"id": id, "beginTime": "2024-12-01", "endTime": "2025-05-01"})
        data = json.loads(response.text)
        dic.update({entry["eduName"]: f'￥{entry["salaryNum"]}/月' for entry in data["data"]})

        with open("output.jl", "a", encoding="utf-8") as f:
            f.write(json.dumps(dic, ensure_ascii=False) + "\n")

        with open("crawled_urls.txt", "a", encoding="utf-8") as f:
            f.write(job["url"] + "\n")

        # time.sleep(0.1)
    except Exception as e:
        print(f"Error processing job {job['url']}: {e}")
        continue

