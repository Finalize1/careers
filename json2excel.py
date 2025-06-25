import pandas as pd
import json


def json_to_excel(
    input_json,
    output_excel,
    json_lines=False,
):
    # 读取JSON文件
    with open(input_json, "r", encoding="utf-8") as f:
        if json_lines:
            # 处理JSON Lines格式
            data = [json.loads(line) for line in f if line.strip()]
        else:
            # 处理普通JSON格式
            data = json.load(f)

    new_data = []
    # 把data中的所有key的冒号都去掉
    for i in data:
        new_data.append({key.replace("：", ""): value for key, value in i.items()})

    # 将JSON数据转换为DataFrame
    df = pd.DataFrame(new_data)

    # 写入Excel文件
    df.to_excel(output_excel, index=False, engine="openpyxl")
    print(f"JSON已成功转换为Excel文件: {output_excel}")


# 使用示例
if __name__ == "__main__":
    li = [
        "yl1001/output.jl",
    ]
    for i in li:
        json_to_excel(i, i.split(".")[0] + ".xlsx", i.endswith(".jl"))
