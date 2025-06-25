import json
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.output_parsers import StrOutputParser
import logging
import re

def remove_special_characters(text):
    # 定义正则表达式，匹配大小括号和分号并替换为空字符串
    pattern = r'[();:：{}""]'
    return re.sub(pattern, '', text)


# 配置日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# 创建日志记录器
logger = logging.getLogger(__name__)


questionDict = {"1":"你所读的专业是什么？在校GPA和排名如何？",
                "2":"你是否有实习经历？请列出公司名称、职位名称、工作时间、主要职责及成果。",
                "3":"你是否参与过重要项目？请描述项目名称、项目时间、角色、工作内容及成果。",
                "4":"你掌握哪些专业技能或工具？请按熟练程度列举。",
                "5":"你是否获得过相关证书或奖项？请提供名称及获得时间",
                "6":"请用3-5个关键词概括你的核心竞争力（如专业技能、性格优势等）。",
                "7":"是否有其他附加信息需要补充？如语言能力、兴趣爱好或志愿者经历等。",
                "8":"请提供你的出生日期、联系电话、邮箱地址，以便通过简历联系你？"}

local_llm = "qwen2.5:7b"
# LLM
llm = ChatOllama(base_url="http://127.0.0.1:11434", model=local_llm, temperature=0)

prompt_question1 = PromptTemplate(
    template="""
    请你根据与大学生的对话，生成教育背景，并返回json格式。scoreRanking对应的是在校GPA和排名。如果有多个学习经历，请都包括进去。如果对话内容中的回答是空的或者无或者是无关的，请返回空的json,请不要无中生有。
    1.返回的json格式
    {{"educationExperienceList": 
        [
          {{
            "education": "",
            "schoolName": "",
            "specialtyName": "",
            "starDate": "",
            "endDate": "",
            "scoreRanking": ""
          }}
        ]
    }}
    2.对话内容是：
    {question}
        """,
    input_variables=["question"],
)
llm_question1 = prompt_question1 | llm | JsonOutputParser()

prompt_question2 = PromptTemplate(
    template="""
    请你根据与大学生的对话，生成实习背景，并返回json格式。industry对应的是职位名称或者项目名称。如果有多个实习经历，请都包括进去。如果对话内容中的回答是空的或者无或者是无关的，请返回空的json,请不要无中生有。
    1.返回的json格式
    {{"projectExperienceList": 
        [
            {{
               "companyName": "",
               "jobDescribe": "",
               "industry": "",
               "starDate": "",
               "endDate": ""
            }}
        ]
    }}
    2.对话内容是：
    {question}
        """,
    input_variables=["question"],
)

llm_question2 = prompt_question2 | llm | JsonOutputParser()

prompt_question3 = PromptTemplate(
    template="""
    请你根据与大学生的对话，生成工作项目背景，并返回json格式。industry对应的是职位名称或者项目名称。如果有多个工作项目经历，请都包括进去。
    1.返回的json格式
    {{"internshipExperienceList": 
        [
            {{
                "companyName": "",
                "jobDescribe": "",
                "industry": "",
                "starDate": "",
                "endDate": ""
            }}
        ]
    }}
    2.对话内容是：
    {question}
    重要提示:如果对话内容中的回答是空的或者无，请返回空的json,请不要无中生有。
        """,
    input_variables=["question"],
)

llm_question3 = prompt_question3 | llm | JsonOutputParser()

prompt_question4 = PromptTemplate(
    template="""
    请你根据与大学生的对话，生成技能或工具背景，并返回json格式。如果对话内容中的回答是空的或者无，请返回空的json,请不要无中生有。
    1.返回的json格式
    {{
        "skill": ["xxx","xxx"]
    }}
    2.对话内容是：
    {question}
        """,
    input_variables=["question"],
)

llm_question4 = prompt_question4 | llm | JsonOutputParser()

prompt_question5 = PromptTemplate(
    template="""
    请你根据与大学生的对话，生成证书背景，并返回json格式。如果有多个证书，请都返回。如果对话内容中的回答是空的或者无或者是无关的，请返回空的json,请不要无中生有。
    1.返回的json格式
    {{
        "certificate": [
          {{
            "certificateName": "",
            "receiveDate": ""
          }}
        ]
    }}
    2.对话内容是：
    {question}
        """,
    input_variables=["question"],
)

llm_question5 = prompt_question5 | llm | JsonOutputParser()

prompt_question6 = PromptTemplate(
    template="""
    请你根据与大学生的对话，生成个人强项背景，personalStrength的内容是字符串，并返回json格式。如果对话内容中的回答是空的或者无或者是无关的，请返回空的json,请不要无中生有。
    1.返回的json格式
    {{
        "personalStrength": ""
    }}
    2.对话内容是：
    {question}
        """,
    input_variables=["question"],
)

llm_question6 = prompt_question6 | llm | JsonOutputParser()

prompt_question7 = PromptTemplate(
    template="""
    请你根据与大学生的对话，生成附加信息，并返回json格式。如果对话内容中的回答是空的或者无或者是无关的，请返回空的json,请不要无中生有。
    1.返回的json格式
    {{
        "attach": ""
    }}
    2.对话内容是：
    {question}
    重要提示：attach对应value内容为字符串，请不要返回数组或者字典，请关注键值的类型都是string。
        """,
    input_variables=["question"],
)

llm_question7 = prompt_question7 | llm | JsonOutputParser()

prompt_question8 = PromptTemplate(
    template="""
    请你根据与大学生的对话，生成个人信息，并返回json格式。如果对话内容中的回答是空的或者无或者是无关的，请返回空的json,请不要无中生有。
    1.返回的json格式
    {{
        "name": "",
        "mobile": "",
        "email": "",
        "birthday": ""
    }}
    2.对话内容是：
    {question}
        """,
    input_variables=["question"],
)

llm_question8 = prompt_question8 | llm | JsonOutputParser()

app = FastAPI()

class QuestionAnswer(BaseModel):
    questionCode: str
    answer: str

async def call_llm(func, qa):
    return await func.ainvoke({"question": qa})

async def call_analyze(questionId, qa):
    if questionId == "1":
        result_llm = await call_llm(llm_question1, qa)
        logger.debug("id:1")
        logger.debug(result_llm)
        return "1",result_llm

    if questionId == "2":
        result_llm = await call_llm(llm_question2, qa)
        logger.debug("id:2")
        logger.debug(result_llm)
        return "2",result_llm

    if questionId == "3":
        result_llm = await call_llm(llm_question3, qa)
        logger.debug("id:3")
        logger.debug(result_llm)
        return "3",result_llm

    if questionId == "4":
        result_llm = await call_llm(llm_question4, qa)
        logger.debug("id:4")
        logger.debug(result_llm)
        return "4",result_llm

    if questionId == "5":
        result_llm = await call_llm(llm_question5, qa)
        logger.debug("id:5")
        logger.debug(result_llm)
        return "5",result_llm

    if questionId == "6":
        result_llm = await call_llm(llm_question6, qa)
        logger.debug("id:6")
        logger.debug(result_llm)
        return "6",result_llm

    if questionId == "7":
        result_llm = await call_llm(llm_question7, qa)
        logger.debug("id:7")
        logger.debug(result_llm)
        return "7",result_llm

    if questionId == "8":
        result_llm = await call_llm(llm_question8, qa)
        logger.debug("id:8")
        logger.debug(result_llm)
        return "8",result_llm

async def high_concurrency_call(questionId_qa_pairs):
    tasks = []
    for questionId, qa in questionId_qa_pairs:
        task = call_analyze(questionId, qa)
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    return results

def parse_json(results,json_result):
    try:
        for item in results:
            try:
                item or item[0] is None or item[1] is None
            except Exception as e:
                continue
            id = item[0]
            data = item[1]
            logger.debug("解析前的数据是:"+id+"   "+json.dumps(data))
            if(id == "1"):
                try:
                    tag = "educationExperienceList"
                    for key,value in data.items():
                        for item in value:
                            data = {}
                            for key1,value1 in item.items():
                                if(key1 in ["education","schoolName","specialtyName","starDate","endDate","scoreRanking"]):
                                    data[key1] = value1
                            json_result["data"][tag].append(data)
                except Exception as e:
                    logger.error("解析educationExperienceList错误")
                    logger.error(e)
                    continue
            if(id == "2"):
                try:
                    tag = "internshipExperienceList"
                    for key,value in data.items():
                        for item in value:
                            data = {}
                            for key1,value1 in item.items():
                                if(key1 in ["companyName","jobDescribe","industry","starDate","endDate"]):
                                    data[key1] = value1
                            json_result["data"][tag].append(data)
                except Exception as e:
                    logger.error("解析projectExperienceList错误")
                    logger.error(e)
                    continue
            if(id == "3"):
                try:
                    tag = "projectExperienceList"
                    for key,value in data.items():
                        for item in value:
                            data = {}
                            for key1,value1 in item.items():
                                if(key1 in ["companyName","jobDescribe","industry","starDate","endDate"]):
                                    data[key1] = value1
                            json_result["data"][tag].append(data)
                except Exception as e:
                    logger.error("解析internshipExperienceList错误")
                    logger.error(e)
                    continue

            if(id =="4"):
                try:
                    tag = "skill"
                    for key, value in data.items():
                        for item in value:
                            data = item
                            json_result["data"][tag].append(data)
                except Exception as e:
                    logger.error("解析skill错误")
                    logger.error(e)
                    continue

            if(id == "5"):
                try:
                    tag = "certificate"
                    for key,value in data.items():
                        for item in value:
                            data = {}
                            for key1,value1 in item.items():
                                if(key1 in ["certificateName","receiveDate"]):
                                    data[key1] = value1
                            json_result["data"][tag].append(data)
                except Exception as e:
                    logger.error("解析certificate错误")
                    logger.error(e)
                    continue

            if(id == "6"):
                try:
                    tag = "personalStrength"
                    for key,value in data.items():
                        if(key==tag):
                            json_result["data"][tag]=remove_special_characters(value)
                except Exception as e:
                    logger.error("解析personalStrength错误")
                    logger.error(e)
                    continue

            if(id == "7"):
                try:
                    tag = "attach"
                    for key, value in data.items():
                        if (key == tag):
                            json_result["data"][tag]=remove_special_characters(value)
                except Exception  as e:
                    logger.error("解析attach错误")
                    logger.error(e)
                    continue
            if(id == "8"):
                try:
                    tag = ["name","mobile","email","birthday"]
                    for key,value in data.items():
                            if(key in tag):
                                json_result["data"][key]=value
                except Exception as e:
                    logger.error("解析个人信息错误")
                    logger.error(e)
                    continue

    except Exception as e:
        logger.error("解析生成json错误")
        logger.error(e)


@app.get("/items/{item_id}")
async def read_root(item_id: int):
    return {}

@app.post("/api/v1/ai/generateAiResume")
async def generate(answers: list[QuestionAnswer]):
    json_result = {
        "code": 0,
        "msg": "",
        "success": True,
        "data": {
            "name": "",
            "mobile": "",
            "email": "",
            "birthday": "",
            "personalStrength": "",
            "projectExperienceList": [
            ],
            "internshipExperienceList": [
            ],
            "certificate": [
            ],
            "educationExperienceList":[
            ],
            "skill": [
            ],
            "attach": ""
        }
    }
    try:
        qas = []
        for answer in answers:
            # 将键值对转为字符串
            answer_dict = answer.dict()
            questionCode = answer_dict["questionCode"]
            question = questionDict[answer_dict["questionCode"]]
            answer = answer_dict["answer"]
            qa = "问题:"+question+"    "+"回答:"+answer
            qas.append((questionCode,qa))
            logger.debug(questionCode+"  "+qa)
        results =await high_concurrency_call(qas)
        if(not results):
            return  json_result
        parse_json(results,json_result)
        logger.debug("生成成功")
        return  json_result
    except Exception as e:
        logger.error("错误信息")
        logger.error(e)
        return {}

if __name__ == "__main__":
    uvicorn.run(app='ResumeGeneration:app', host='0.0.0.0', port=8101, reload=True)

