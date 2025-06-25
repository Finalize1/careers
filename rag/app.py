# app.py

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from rag.embedding_module import encode_text
from rag.milvus_module import collection

app = FastAPI()

def build_job_text(job: dict) -> str:
    """
    拼接岗位多列信息生成语义文本
    """
    title = job.get("title", "暂无职位名称")
    desc = job.get("description", "暂无简介")
    edu = job.get("education", "无学历要求")
    major = job.get("major", "不限专业")
    skills = job.get("skills", "无明确技能要求")

    text = (
        f"职位名称：{title}。"
        f"职位简介：{desc}。"
        f"学历要求：{edu}。"
        f"专业要求：{major}。"
        f"专业技能：{skills}。"
    )
    return text

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>岗位推荐 Demo</title></head>
    <body>
        <h2>输入一句话，推荐匹配岗位</h2>
        <textarea id="query" rows="4" cols="50"></textarea><br>
        <button onclick="sendQuery()">推荐</button>
        <pre id="result"></pre>
        <script>
            async function sendQuery() {
                const q = document.getElementById("query").value;
                const res = await fetch("/recommend", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({"query": q})
                });
                const data = await res.json();
                document.getElementById("result").innerText = JSON.stringify(data, null, 2);
            }
        
            // 绑定回车事件
            document.getElementById("query").addEventListener("keydown", function(e) {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendQuery();
                }
            });
        </script>
    </body>
    </html>
    """

@app.post("/recommend")
async def recommend(request: Request):
    data = await request.json()
    query = data.get("query", "")
    query_vec = encode_text(query)

    results = collection.search(
        data=[query_vec],
        anns_field="embedding",
        param={"metric_type": "IP", "params": {"nprobe": 10}},
        limit=5,
        output_fields=["job_id", "title", "description", "education", "major", "skills"]
    )

    hits = []
    for result in results[0]:
        hits.append({
            "job_id": result.entity.job_id,
            "title": result.entity.title,
            "description": result.entity.description,
            "education": result.entity.education,
            "major": result.entity.major,
            "skills": result.entity.skills,
            "score": result.score
        })

    return JSONResponse(content={"query": query, "recommendations": hits})
