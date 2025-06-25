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

def clean_llm_output(output):
    """Remove thinking sections from LLM output"""
    import re

    if hasattr(output, "content"):
        text = output.content
    else:
        text = str(output)
    cleaned_output = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    cleaned_output = cleaned_output.strip()
    return cleaned_output

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

local_llm = "qwen3:8b"
# LLM
llm = ChatOllama(base_url="http://127.0.0.1:11434", model=local_llm, temperature=0)

prompt_experience = PromptTemplate(
    template="""
    从我提供的文本中提取出经历信息，包括公司名称、职位名称、职位描述、开始日期、结束日期等信息，并返回json格式。
    对于jobDescribe，已知我的期望岗位是{expectedJob}。请你作为一位资深的简历优化专家，具有丰富的人力资源和技术背景知识，对我提供的工作经历描述进行专业化的润色和扩充，使其更具吸引力和说服力：
        - 使用更专业、更精准的技术术语
        - 强调成果导向的表述（如何解决问题、带来什么价值），但不要给出过于具体的文本中没有的数字信息
        - 突出核心技能和专业能力
        - 对于成果描述如果没有具体数据，不要假设文本中没有提供的数据
        - 体现个人在团队中的价值和领导力
        - 保持内容的真实性和专业性
        
    1.返回的json格式
    {{"experienceList": 
        [
            {{
                "companyName": "",
                "jobName": "",
                "jobDescribe": "",
                "starDate": "",
                "endDate": ""
            }}
        ]
    }}
    2.对话内容是：
    {experienceDescribe}
        """,
    input_variables=["expectedJob", "experienceDescribe"],
)

llm_experience = prompt_experience | llm | (lambda x: clean_llm_output(x)) | JsonOutputParser()

prompt_sum = PromptTemplate(
    template="""
    以下文本是多段项目经历，从文本中提取出个人优势信息，主要基于项目经历进行总结，要求内容能够体现出我在{expectedJob}这一求职意向领域的优势和技能。
    1.返回的json格式
    {{
        "personalSummarization": ""
    }}
    2.对话内容是：
    {experienceDescribe}
    """,
    input_variables=["expectedJob", "experienceDescribe"],
)

llm_sum = prompt_sum | llm | (lambda x: clean_llm_output(x)) | JsonOutputParser()

app = FastAPI()

class QuestionAnswer(BaseModel):
    expectedJob: str
    experienceDescribe: str

async def call_llm(func, expJob, expDescribe):
    return await func.ainvoke({ "expectedJob": expJob, "experienceDescribe": expDescribe})

async def call_analyze(expJob, expDescribe):
    tasks = [
        call_llm(llm_experience, expJob, expDescribe),
        call_llm(llm_sum, expJob, expDescribe)
    ]
    results = await asyncio.gather(*tasks)
    return results

@app.get("/items/{item_id}")
async def read_root(item_id: int):
    return {}

@app.post("/api/v1/ai/generateAiResume")
async def generate(answers: QuestionAnswer):
    json_result = {
        "code": 0,
        "msg": "",
        "success": True,
        "data": {
            "personalSummarization": "",
            "experienceList": [],
        }
    }
    try:
        logger.debug(f"接收到的内容：{answers.expectedJob, answers.experienceDescribe[:100]}...") # 只记录前100个字符

        results = await call_analyze(answers.expectedJob, answers.experienceDescribe)

        if not results:
            return json_result

        try:
            experienceInfo = results[0]
            if "experienceList" in experienceInfo:
                json_result["data"]["experienceList"] = experienceInfo["experienceList"]
            logger.debug(f"经历解析结果：{json.dumps(experienceInfo)}")
        except Exception as e:
            logger.error(f"解析经历错误：{str(e)}")

        try:
            otherInfo = results[1]
            if "personalSummarization" in otherInfo:
                json_result["data"]["personalSummarization"] = otherInfo["personalSummarization"]
            logger.debug(f"个人总结解析结果：{json.dumps(otherInfo)}")
        except Exception as e:
            logger.error(f"解析个人总结错误：{str(e)}")
        
        logger.debug("简历生成成功")
        return json_result
    except Exception as e:
        logger.error(f"处理过程出现错误: {str(e)}")
        return {
            "code": 500,
            "msg": "处理过程出现错误",
            "success": False,
            "data": {}
        }

if __name__ == "__main__":
    uvicorn.run(app='ResumeGeneration:app', host='0.0.0.0', port=8101, reload=True)

