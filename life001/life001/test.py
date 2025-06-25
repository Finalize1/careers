import json


def merge_dicts_high_performance(dicts):
    result = {}
    for d in dicts:
        for k, v in d.items():
            if v != "":  # 只更新非空值
                result[k] = v
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
    merged = [merge_dicts_high_performance(v) for k, v in grouped_data.items()]
    json.dump(merged, f, ensure_ascii=False, indent=4)
