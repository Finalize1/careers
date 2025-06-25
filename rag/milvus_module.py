# milvus_module.py

from pymilvus import connections, utility, Collection, FieldSchema, CollectionSchema, DataType

COLLECTION_NAME = "job_recommendation"

connections.connect("default", host="localhost", port="19530")

if utility.has_collection(COLLECTION_NAME):
    collection = Collection(COLLECTION_NAME)
    print(f"✅ Collection `{COLLECTION_NAME}` 已存在")
else:
    fields = [
        FieldSchema(name="job_id", dtype=DataType.INT64, is_primary=True, auto_id=False),
        FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=200),
        FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=2000),
        FieldSchema(name="education", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="major", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="skills", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=512)
    ]
    schema = CollectionSchema(fields, description="Job Recommendation Collection (Multi-column)")
    collection = Collection(COLLECTION_NAME, schema)
    print(f"✅ Created Collection `{COLLECTION_NAME}`")

collection.load()
