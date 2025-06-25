# llm_client.py

def generate_answer(question: str, context_docs: list):
    """
    TODO: 这里将来可以对接真实 LLM，如 OpenAI、LLama、ChatGLM 等
    现在先用 mock 文本拼接
    """
    context_text = "\n".join([doc["text"] for doc in context_docs])
    answer = (
        f"【模拟答案】根据检索到的上下文，我推测：\n"
        f"{context_text}\n\n"
        f"因此，关于你的问题「{question}」，建议进一步验证后使用。"
    )
    return answer
