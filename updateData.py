import os
import asyncio
import aio_pika
import pika
import time
import logging
from pymilvus import connections, Collection, utility,MilvusClient, DataType,CollectionSchema,FieldSchema
import ollama
import json
import numpy as np
ollama.api_base = "http://192.168.0.2:11434"
from datetime import datetime

# 配置日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tool/updateData.log"),
        logging.StreamHandler()
    ]
)
# 创建日志记录器
logger = logging.getLogger(__name__)

# RabbitMQ 配置信息
host = '192.168.0.237'
port = 5672
username = 'root'
password = '2lOGwQvZH2L8dJ4x'

#测试环境
# host = '192.168.0.218'
# port = 5672
# username = 'root'
# password = 'root'

queue_name = 'event_to_recommend'
collection = None

data = {
    "id": 1,
    "name": "Go语言研讨会",
    "organizer": "Go社区",
    "deletedAt": "",
    "status":1,
    "tags": [
        {
            "name": "Go",
            "title": "Go语言",
            "explain": "一种编程语言",
            "groupName": "技术",
            "categoryName": "编程"
        },
        {
            "name": "研讨会",
            "title": "技术分享",
            "explain": "技术交流活动",
            "groupName": "活动",
            "categoryName": "技术"
        }
    ],
    "announcements": [
        {
            "name": "开场致辞",
            "announcement": "欢迎各位参加Go语言研讨会"
        },
        {
            "name": "技术分享",
            "announcement": "我们将讨论最新的Go语言特性"
        }
    ],
    "qualities": [
        {
            "name": "视频质量",
            "quality": "高清"
        },
        {
            "name": "音频质量",
            "quality": "立体声"
        }
    ],
    "startAt": "2025-10-01 08:05:01",
    "endAt": "2025-10-01 08:05:01",
    "joinStartAt": "2025-10-01 08:05:01",
    "joinEndAt": "2025-10-01 08:05:01"
}

def strptime(data):
    if(data):
        result = datetime.strptime(data,"%Y-%m-%d %H:%M:%S").timestamp()
        return result
    else:
        return None

def flatten_json(json_obj):

        logger.debug("解析json开始")
        tags = ""
        json_obj = json.loads(json_obj)
        if isinstance(json_obj, dict):
            for key, value in json_obj.items():
                if(key =="id"):
                    id = value
                if(key == "name"):
                    name = value
                if(key == "tags" ):
                    tags = ""
                    for item in value:
                        for k,v in item.items():
                            if(k == "name"):
                                tags += f"{v} "
                if(key == "startAt"):
                    startAt = 0 if strptime(value)==None else strptime(value)
                if(key == "endAt"):
                    endAt = 0 if strptime(value)==None else strptime(value)
                if(key == "deletedAt"):
                    deletedAt = strptime(value)
                if(key == "status"):
                    status = value
                if(key == "joinStartAt"):
                    joinStartAt = strptime(value)
                if(key == "joinEndAt"):
                    joinEndAt = strptime(value)
        logger.debug("解析json结束")
        return name,id,tags,startAt,endAt,deletedAt,status,joinStartAt,joinEndAt

def initMilvus():

        logger.debug("初始化milvus开始")
        connections.connect(
            alias="default",
            host="192.168.0.2",
            port="19530"
        )
        # 获取所有集合的名称
        collection_name = "ActivityRecommendation"
        collection_names = utility.list_collections()
        print("所有集合名称:", collection_names)
        global collection
        if(collection_name in collection_names):
            collection = Collection("ActivityRecommendation")
        else:
            schema = CollectionSchema([
                FieldSchema("id", DataType.INT64, is_primary=True,auto_id=True),
                FieldSchema("vector", DataType.FLOAT_VECTOR, dim=1024),
                FieldSchema("game_id", DataType.INT64),
                FieldSchema("name", DataType.VARCHAR, max_length=65535),
                FieldSchema("tags", DataType.VARCHAR,max_length=65535),
                FieldSchema("startAt", DataType.DOUBLE,max_length=1024),
                FieldSchema("endAt", DataType.DOUBLE,max_length=1024),
                FieldSchema("joinStartAt", DataType.DOUBLE, max_length=1024),
                FieldSchema("joinEndAt", DataType.DOUBLE, max_length=1024),
                FieldSchema("status", DataType.INT64)
            ])
            collection = Collection(
                name=collection_name,
                schema=schema
            )
            index_params = {
                "metric_type": "COSINE",
            }

            # Create an index on the vector field
            collection.create_index(
                field_name="vector",
                index_params=index_params,
                timeout=None
            )
        collection.load()
        logger.debug("初始化milvus结束")

def updateMilvus(data,deletedAt):

        logger.debug("更新milvus开始")
        collection.load()
        game_id = data["game_id"]
        output_fields = ["name","id"]
        result = collection.query(
            expr=f"game_id == {game_id}",
            output_fields=output_fields
        )
        if(deletedAt):
            if(result):
                id = result[0]["id"]
                collection.delete(f"id =={id} ")
        else:
            if(result):
                data["id"] = result[0]["id"]
                collection.upsert(data)
            else:
                collection.insert(data)
        collection.flush()
        logger.debug("更新milvus结束")

def embeding(text):
    # 调用 bge-m3 模型生成嵌入向量

        logger.debug("embeding开始")
        response = ollama.embed(model="bge-m3:latest", input=text)
        # 提取嵌入向量
        embeddings = response['embeddings']
        # 打印嵌入向量
        logger.debug("embeding结束")
        return embeddings[0]

def updateData(data):

        name,id,tags,startAt,endAt,deletedAt,status,joinStartAt,joinEndAt = flatten_json(data)
        logger.debug(f"解析后的tags:{tags}")
        if(tags):
            vector = embeding(tags)
            updateMilvus({"vector":vector,"game_id":id,"tags":tags,"startAt":startAt,"endAt":endAt,"name":name,"status":status,"joinStartAt":joinStartAt,"joinEndAt":joinEndAt},deletedAt)
        else:
            logger.debug("tags为空，更新数据无效")

def nowTime():
    now = datetime.now()
    date= now.strftime("%Y-%m-%d %H:%M:%S")
    return date

def write_text_file(file_path, content):
    try:
        with open(file_path, 'a', encoding='utf-8') as file:
            time = nowTime()
            content = content.replace("\n","").replace("\r","")
            file.write(time+" @ "+content+"\n")
        print(f"成功写入文本文件: {file_path}")
    except Exception as e:
        print(f"写入文本文件时出错: {e}")

async def subscribe():
    try:
        # 建立连接
        connection = await aio_pika.connect_robust(
            host=host,
            port=port,
            virtualhost="apis",
            login=username,
            password=password,
            heartbeat=60
        )

        async with connection:
            # 创建通道
            channel = await connection.channel()

            # 声明扇形交换机
            exchange_name = 'event'
            exchange = await channel.declare_exchange(
                exchange_name,
                aio_pika.ExchangeType.FANOUT,
                durable=True
            )

            # 声明一个临时队列，当消费者断开连接时，队列会自动删除
            queue = await channel.declare_queue(exclusive=True)

            # 绑定队列到交换机
            await queue.bind(exchange)

            async def callback(message: aio_pika.IncomingMessage):
                async with message.process():
                    try:
                        body = message.body.decode('utf-8')
                        logger.debug(f"接收到消息: {body}")
                        # 由于 write_text_file 是同步函数，若要充分利用异步特性，可考虑将其改为异步函数
                        # 这里暂时直接调用
                        write_text_file("./data/data.txt", body)
                        updateData(body)
                    except Exception as e:
                        logger.error(f"处理消息时出现错误: {e}")

            # 开始消费消息
            await queue.consume(callback)

            print("Waiting for messages. To exit press CTRL+C")
            try:
                await asyncio.Future()
            finally:
                if collection:
                    collection.release()
    except Exception as e:
        logger.error(f"发生错误: {e}")

if __name__ == '__main__':
    initMilvus()
    asyncio.run(subscribe())