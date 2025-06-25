# init_data.py

from pymilvus import connections, utility, FieldSchema, CollectionSchema, DataType, Collection
from embedding_module import EmbeddingSingleton

COLLECTION_NAME = "job_recommendation"

# 连接 Milvus
connections.connect("default", host="localhost", port="19530")

# 如果存在则先删除（可选）
if utility.has_collection(COLLECTION_NAME):
    print(f"⚠️ Collection `{COLLECTION_NAME}` 已存在，先删除")
    utility.drop_collection(COLLECTION_NAME)

# 创建新 Collection，包含多列
fields = [
    FieldSchema(name="job_id", dtype=DataType.INT64, is_primary=True, auto_id=False),
    FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=200),
    FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=2000),
    FieldSchema(name="education", dtype=DataType.VARCHAR, max_length=50),
    FieldSchema(name="major", dtype=DataType.VARCHAR, max_length=200),
    FieldSchema(name="skills", dtype=DataType.VARCHAR, max_length=500),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=512)
]

schema = CollectionSchema(fields, description="Job Recommendation Collection with Multi-column")
collection = Collection(COLLECTION_NAME, schema)
print(f"✅ Created Collection `{COLLECTION_NAME}`")

import pandas as pd

file = pd.read_excel("../baike/前程无忧.xlsx")

# 选取部分列
jobs = file[["职位名称", "职位简介", "学历要求", "专业要求", "专业技能"]]
# 重命名列
jobs.columns = ["title", "description", "education", "major", "skills"]
# 添加 job_id 列
jobs["job_id"] = range(1, len(jobs) + 1)
# 移到第一列
jobs = jobs[["job_id", "title", "description", "education", "major", "skills"]]
# 转换为字典列表
jobs = jobs.to_dict(orient="records")

import math

def safe_str(val, default=""):
    if pd.isna(val) or (isinstance(val, float) and math.isnan(val)):
        return default
    return str(val)

for job in jobs:
    for key in ["title", "description", "education", "major", "skills"]:
        job[key] = safe_str(job.get(key), default="无")

jobs = jobs  # 保持后续逻辑不变

# 拼接文本
def build_job_text(job: dict) -> str:
    title = job.get("title", "暂无职位名称")
    desc = job.get("description", "暂无简介")
    edu = job.get("education", "无学历要求")
    major = job.get("major", "不限专业")
    skills = job.get("skills", "无明确技能要求")
    return (
        f"职位名称：{title}。"
        f"职位简介：{desc}。"
        f"学历要求：{edu}。"
        f"专业要求：{major}。"
        f"专业技能：{skills}。"
    )

texts = [build_job_text(job) for job in jobs]

# 初始化 Embedding
embedder = EmbeddingSingleton.get_model()
vectors = embedder.encode(texts, normalize_embeddings=True, show_progress_bar=True)

# 插入数据
entities = [
    [job["job_id"] for job in jobs],
    [job["title"] for job in jobs],
    [job["description"] for job in jobs],
    [job["education"] for job in jobs],
    [job["major"] for job in jobs],
    [job["skills"] for job in jobs],
    vectors.tolist()
]

mr = collection.insert(entities)
print(f"✅ Inserted {mr.insert_count} jobs!")

# 创建索引
index_params = {
    "metric_type": "IP",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 128}
}
collection.create_index(field_name="embedding", index_params=index_params)
collection.load()

print("🎉 数据初始化完成，Milvus 已可用于搜索！")
