import json

import pandas as pd

with open("jobs.jl", "r", encoding="utf-8") as f:
    jobs = [json.loads(line) for line in f]

dics = pd.DataFrame()
for job in jobs:
    dic = {}
    for key, value in job.items():
        if key == "岗位要求":
            first_key = next(iter(value))
            first_value = value[first_key]
            dic.update(first_value)
            dic["专业技能"] = '，'.join(dic["专业技能"].keys())

        else:
            dic[key] = value


    # 将所有dic转成DataFrame
    df = pd.DataFrame([dic])
    dics = pd.concat([dics, df], ignore_index=True)
print(dics)
dics.to_excel("jobs.xlsx", index=False)
