import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os

import pandas as pd
import requests
from tqdm import tqdm

# 显示pd的完整行列
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
# 设置pd的显示宽度
pd.set_option('display.width', 1000)

mapping = {
    1: "数学建模",
    13: "船舶海洋",
    14: "材料高分子",
    15: "环境能源",
    34: "大数据",
    12: "航空航天",
    11: "交通车辆",
    10: "土木建筑",
    9: "工程机械",
    6: "计算机&信息技术",
    2: "程序设计",
    4: "机器人",
    5: "电子&自动化",
    19: "外语",
    36: "艺术素养",
    20: "UI设计",
    24: "演讲主持&辩论",
    33: "科技文化艺术节",
    32: "体育",
    22: "服装设计",
    23: "模特",
    21: "工业&创意设计",
    25: "歌舞书画&摄影",
    31: "电子竞技",
    35: "力学",
    18: "化学化工",
    17: "物理",
    16: "数学",
    30: "健康生命&医学",
    26: "商业",
    3: "创业",
    8: "创青春",
    29: "社会综合",
    28: "职业技能",
    27: "环保公益",
    7: "挑战杯",
}

if not os.path.exists('crawled_name.txt'):
    with open('crawled_name.txt', 'w', encoding='utf-8') as f:
        f.write('')

with open('crawled_name.txt', 'r', encoding='utf-8') as f:
    crawled_names = set(line.strip() for line in f)

# 日期转时间戳
date_str = '2025-01-01 00:00:00'
timestamp = int(time.mktime(time.strptime(date_str, '%Y-%m-%d %H:%M:%S')))


def fetch_contest(k):
    url = f'https://apiv4buffer.saikr.com/api/pc/contest/lists?page=1&limit=1000&univs_id=&class_id={str(k)}&level=0&sort=0'

    response = requests.get(url)
    data = response.json()
    contests = data['data']['list']

    # 赛事名称	竞赛类别	赛氪赛事地址	主办方	状态	报名时间	比赛时间
    df = pd.DataFrame(contests)
    # 筛选出特定列
    df = df[['contest_name', 'contest_class_second_id', 'contest_url', 'organiser', 'time_name', 'regist_start_time',
             'regist_end_time', 'contest_start_time', 'contest_end_time']]
    df['contest_class_second_id'] = mapping[k]
    df['contest_url'] = df['contest_url'].apply(lambda x: f'https://new.saikr.com/{str(x)}')
    df['regist_start_time'] = df['regist_start_time'].apply(
        lambda x: time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(x)))
    df['regist_end_time'] = df['regist_end_time'].apply(lambda x: time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(x)))
    df['contest_start_time'] = df['contest_start_time'].apply(
        lambda x: "待定" if x == 0 else time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(x)))
    df['contest_end_time'] = df['contest_end_time'].apply(
        lambda x: "待定" if x == 0 else time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(x)))
    # 筛选出报名时间在2025年1月1日之后的赛事
    df = df[df['regist_start_time'] >= '2025-01-01 00:00:00']
    # 去除比赛结束的
    df = df[df['time_name'].isin(['正在报名', '比赛进行中', '即将报名', '即将开赛'])]
    # 过滤掉已经爬取过的赛事
    df = df[~df['contest_name'].isin(crawled_names)]
    # 修改列名
    df.columns = ['赛事名称', '竞赛类别', '赛氪赛事地址', '主办方', '状态', '报名开始时间', '报名结束时间',
                  '比赛开始时间',
                  '比赛结束时间']
    df['报名时间'] = df['报名开始时间'] + ' ~ ' + df['报名结束时间']
    df['比赛时间'] = df['比赛开始时间'] + ' ~ ' + df['比赛结束时间']

    df.drop(columns=['报名开始时间', '报名结束时间', '比赛开始时间', '比赛结束时间'], inplace=True)

    return df


def agg_func(x):
    if x.name == '竞赛类别':
        return '、'.join(sorted(set(x)))
    else:
        s = set(x)
        return tuple(s) if len(s) > 1 else next(iter(s))


df_list = []

with ThreadPoolExecutor(max_workers=9) as executor:
    futures = {executor.submit(fetch_contest, k): k for k in mapping.keys()}
    for future in tqdm(as_completed(futures), total=len(mapping)):
        try:
            df = future.result()
            df_list.append(df)
        except Exception as e:
            print(f"类别 {futures[future]} 抓取失败: {e}")

merged_df = pd.concat(df_list).groupby('赛事名称').agg(agg_func).reset_index()

with open('crawled_name.txt', 'a', encoding='utf-8') as f:
    for name in merged_df['赛事名称']:
        f.write(name + '\n')

# 保存到Excel文件，按照年月日时分秒
merged_df.to_excel(f"挑战杯_{time.strftime('%Y%m%d_%H%M%S', time.localtime())}.xlsx", index=False)
