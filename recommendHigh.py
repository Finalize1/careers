import uvicorn
from fastapi import FastAPI, Body
from pydantic import BaseModel
from pymilvus import connections, Collection, utiqlity
from datetime import datetime
import logging
import ollama
from typing import List
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
ollama.api_base = "http://192.168.0.2:11434"
# 配置日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tool/recommend.log"),
        logging.StreamHandler()
    ]
)
# 创建日志记录器
logger = logging.getLogger(__name__)

# 初始化 Milvus 连接
connections.connect(alias="default", host="192.168.0.2", port="19530")
collection_name = "ActivityRecommendation"
collection = None
if utility.has_collection(collection_name):
    collection = Collection(collection_name)
    collection.load()
else:
    logger.debug("没有对应的集合")

# 创建线程池
executor = ThreadPoolExecutor(max_workers=50)


def nowTime(time=None):
    if not time:
        now = datetime.now()
        # 格式化为字符串
        date = now.strftime("%Y-%m-%d %H:%M:%S")
        result = datetime.strptime(date, "%Y-%m-%d %H:%M:%S").timestamp()
        return result
    else:
        result = datetime.strptime(time, "%Y-%m-%d %H:%M:%S").timestamp()
        return result


async def initMilvus():
    try:
        logger.debug("开始初始化Milvus")
        # 已经在全局初始化，这里无需重复连接
        logger.debug("初始化Milvus结束")
    except Exception as e:
        logger.error(f"初始化Milvus错误：{e}")


async def search(query_vector, time):
    def _search():
        try:
            logger.debug("search开始")

            search_params = {
                "metric_type": "COSINE",
                "params": {
                    "nprobe": 1024,
                    "radius": 0.2,
                    "range_filter": 1.0
                }
            }

            output_fields = ["id", "name", "game_id"]

            results = collection.search(
                data=[query_vector],
                anns_field="vector",  # 向量字段名
                param=search_params,
                limit=12,  # 返回的结果数量
                expr=f"status ==1 AND joinEndAt > {time}",
                output_fields=output_fields
            )
            parsed_list = []
            for hit in results[0]:
                distance = hit.distance
                game_id = hit.entity.game_id
                parsed_list.append({'id': game_id, 'rank': distance})

            # 根据 distance 从大到小排序
            sorted_list = sorted(parsed_list, key=lambda x: x['rank'], reverse=True)

            priority = 1
            for item in sorted_list:
                item["rank"] = priority
                priority += 1
            logger.debug("search结束")
            return sorted_list
        except Exception as e:
            logger.error(f"search发生错误: {e}")
            return None

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, _search)


async def query(data_search, time):
    def _query():
        try:
            logger.debug("query开始")
            output_fields = ["id", "name", "game_id"]
            game_id_list = []
            if data_search:
                game_num = len(data_search)
            else:
                game_num = 0
            for hit in data_search:
                game_id_list.append(hit["id"])
            residual_num = 12 - game_num
            game_id_str = str(game_id_list)
            results = []
            if game_num < 12:
                results = collection.query(
                    limit=residual_num,
                    expr=f"game_id not in {game_id_str} AND joinEndAt > {time}  ",
                    output_fields=output_fields
                )
            parsed_list = []
            if results:
                for item in results:
                    game_id = item["game_id"]
                    parsed_list.append({'id': game_id, 'rank': 12})
                    game_id_list.append(game_id)
            results2 = []
            if len(parsed_list) < residual_num:
                game_id_str2 = str(game_id_list)
                residual_num2 = residual_num - len(parsed_list)
                results2 = collection.query(
                    limit=residual_num2,
                    expr=f"game_id not in {game_id_str2}  ",
                    output_fields=output_fields
                )

            if results2:
                for item in results2:
                    game_id = item["game_id"]
                    parsed_list.append({'id': game_id, 'rank': 12})

            logger.debug("query结束")
            return parsed_list
        except Exception as e:
            logger.error(f"query发生错误: {e}")
            return None

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, _query)


async def embeding(text):
    def _embeding():
        # 调用 bge-m3 模型生成嵌入向量
        try:
            logger.debug("embeding开始")
            logger.debug("text:"+text)
            response = ollama.embed(model="bge-m3:latest", input=text)
            # 提取嵌入向量
            embeddings = response['embeddings']
            # 打印嵌入向量
            print("嵌入向量:", embeddings)
            logger.debug("embeding结束")
            return embeddings[0]
        except Exception as e:
            logger.error(f"embeding发生错误: {e}")
            return None

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, _embeding)



app = FastAPI()


class RecommendData(BaseModel):
    requirement: List[str]
    interest: List[str]
    property: List[str]


@app.get("/items/{item_id}")
async def read_root(item_id: int):
    return {}


@app.post("/api/v1/ai/recommend")
async def recommend(data: RecommendData):
    try:
        await initMilvus()
        requirement_str = ", ".join(data.requirement)
        interest_str = ", ".join(data.interest)
        property_str = ", ".join(data.property)
        tags = f"{requirement_str} {interest_str}  {property_str}"
        logger.debug("tags:" + tags)
        vector = await embeding(tags)
        if not vector:
            logger.debug("embeding为空")
            return {}
        time = nowTime()
        results_search = await search(vector, time)
        print("search结果为:",results_search)
        results_query = await query(results_search, time)
        if results_search and results_query:
            results_search.extend(results_query)
        elif results_query:
            results_search = results_query
        logger.debug("返回结果:"+json.dumps(results_search))
        return results_search
    except Exception as e:
        logger.error(f"错误信息:{e}")
        return {}

@app.on_event("shutdown")
def release_collection():
    if collection is not None:
        try:
            collection.release()
            logger.debug("Milvus collection 已释放")
        except Exception as e:
            logger.error(f"释放 Milvus collection 时出错: {e}")

if __name__ == "__main__":
    uvicorn.run(app='recommendHigh:app', host='0.0.0.0', port=8100, reload=True)
    