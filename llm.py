from pymilvus import connections, FieldSchema, CollectionSchema, Collection, DataType, utility
from sentence_transformers import SentenceTransformer

# === 1) 定义一个 QA 数据集（示例 20 条） ===
qa_dataset = [
    {
        "text": "BERT是一种基于Transformer的预训练语言模型，用于生成双向上下文表示。",
        "question": "BERT的主要功能是什么？",
        "answer": "BERT用于生成双向上下文表示，提升自然语言理解能力。"
    },
    {
        "text": "GPT是一种自回归生成式语言模型，擅长生成连贯自然的文本。",
        "question": "GPT适合做什么任务？",
        "answer": "GPT适合生成连贯自然的文本，例如对话和写作。"
    },
    {
        "text": "Transformer采用自注意力机制替代了传统RNN结构，实现高效并行计算。",
        "question": "Transformer的创新点是什么？",
        "answer": "Transformer用自注意力机制替代了RNN，实现高效并行。"
    },
    {
        "text": "RNN是循环神经网络，适合处理时间序列和语音等顺序数据。",
        "question": "RNN主要用于什么？",
        "answer": "RNN适合处理时间序列和语音等顺序数据。"
    },
    {
        "text": "LSTM是RNN的改进版本，通过门控机制解决了长依赖问题。",
        "question": "LSTM相对RNN有什么改进？",
        "answer": "LSTM通过门控机制解决了长依赖问题。"
    },
    {
        "text": "GRU是另一种RNN变体，与LSTM相比结构更简单。",
        "question": "GRU与LSTM相比有什么特点？",
        "answer": "GRU结构比LSTM简单，参数更少。"
    },
    {
        "text": "知识图谱通过节点和关系边描述现实世界中的实体和联系。",
        "question": "知识图谱如何建模信息？",
        "answer": "知识图谱用节点表示实体，边表示实体之间的关系。"
    },
    {
        "text": "向量数据库如Milvus用于高效存储和搜索高维向量。",
        "question": "向量数据库的用途是什么？",
        "answer": "向量数据库用于存储和相似度搜索高维向量。"
    },
    {
        "text": "RAG结合了外部文档检索与生成模型，提升了问答准确率。",
        "question": "RAG的结构包含哪些部分？",
        "answer": "RAG由检索模块和生成模型组成。"
    },
    {
        "text": "Prompt Engineering通过设计提示词优化大模型生成效果。",
        "question": "Prompt Engineering的作用是什么？",
        "answer": "Prompt Engineering通过设计提示词优化生成效果。"
    },
    {
        "text": "Tokenization是NLP预处理步骤，将文本切分为词或子词。",
        "question": "NLP中的Tokenization是做什么的？",
        "answer": "Tokenization用于把文本切分为词或子词。"
    },
    {
        "text": "Embedding是把文本映射到向量空间以表示语义信息。",
        "question": "Embedding的作用是什么？",
        "answer": "Embedding把文本映射为向量，捕捉语义信息。"
    },
    {
        "text": "自监督学习利用数据本身生成伪标签，减少人工标注需求。",
        "question": "自监督学习的好处是什么？",
        "answer": "自监督学习减少了人工标注需求。"
    },
    {
        "text": "知识蒸馏让小模型学习大模型的知识，便于模型压缩和部署。",
        "question": "知识蒸馏的用途是什么？",
        "answer": "知识蒸馏用于把大模型的知识迁移给小模型。"
    },
    {
        "text": "云计算提供弹性扩展的计算资源，适合大规模数据处理。",
        "question": "云计算的特点是什么？",
        "answer": "云计算提供弹性计算资源，适合大规模处理。"
    },
    {
        "text": "边缘计算将算力下沉到靠近数据源的设备，降低延迟。",
        "question": "边缘计算的优势是什么？",
        "answer": "边缘计算降低了网络延迟。"
    },
    {
        "text": "生成式AI能根据输入提示自动生成文字、图片或音频内容。",
        "question": "生成式AI可以做什么？",
        "answer": "生成式AI可以自动生成文字、图片或音频内容。"
    },
    {
        "text": "多模态学习结合了来自不同模态的数据，如图像和文本。",
        "question": "多模态学习处理什么类型数据？",
        "answer": "多模态学习结合不同模态的数据，如图像和文本。"
    },
    {
        "text": "大语言模型需要依赖高效的向量检索以实现RAG问答。",
        "question": "大语言模型为何需要向量检索？",
        "answer": "向量检索帮助大模型快速找到相关上下文，实现RAG。"
    },
    {
        "text": "Pinecone是一种云原生向量数据库，支持大规模在线检索。",
        "question": "Pinecone是做什么的？",
        "answer": "Pinecone是一种云向量数据库，支持大规模检索。"
    },
    {
        "text": "Faiss是Facebook开发的高效相似度搜索库。",
        "question": "Faiss是谁开发的？",
        "answer": "Faiss是Facebook开发的。"
    },
    {
        "text": "Attention机制为输入序列分配权重，捕捉关键信息。",
        "question": "Attention机制是做什么的？",
        "answer": "Attention机制通过分配权重捕捉关键信息。"
    },
    {
        "text": "主成分分析（PCA）通过线性变换降低数据维度。",
        "question": "PCA的主要用途是什么？",
        "answer": "PCA用于降低数据维度。"
    },
    {
        "text": "聚类是一种无监督学习方法，用于自动发现数据中的分组。",
        "question": "聚类属于哪种学习？",
        "answer": "聚类属于无监督学习。"
    },
    {
        "text": "异常检测用于识别数据中的异常模式和离群点。",
        "question": "异常检测的目标是什么？",
        "answer": "异常检测用于识别异常模式和离群点。"
    },
    {
        "text": "强化学习通过与环境交互基于奖励学习最优策略。",
        "question": "强化学习的核心思想是什么？",
        "answer": "强化学习通过奖励信号学习最优策略。"
    },
    {
        "text": "自回归模型基于已知历史生成序列的下一个元素。",
        "question": "自回归模型如何生成序列？",
        "answer": "自回归模型基于历史生成下一个元素。"
    },
    {
        "text": "情感分析用于识别文本的情绪倾向，如积极或消极。",
        "question": "情感分析的作用是什么？",
        "answer": "情感分析识别文本情绪倾向。"
    },
    {
        "text": "命名实体识别（NER）用于从文本中提取专有名词和实体。",
        "question": "NER识别什么？",
        "answer": "NER用于识别文本中的专有名词和实体。"
    },
    {
        "text": "语义搜索通过向量相似度寻找相关文本，提升搜索准确度。",
        "question": "语义搜索的优势是什么？",
        "answer": "语义搜索通过向量相似度提升搜索准确度。"
    }
]


# === 2) 连接 Milvus ===
connections.connect("default", host="localhost", port="19530")
collection_name = "qa_test_bge"

# 清理老的 collection
if utility.has_collection(collection_name):
    Collection(collection_name).drop()

# === 3) 加载 BGE 中文模型 ===
model = SentenceTransformer("BAAI/bge-small-zh-v1.5")

# === 4) 准备数据 ===
texts = [item["text"] for item in qa_dataset]
questions = [item["question"] for item in qa_dataset]
answers = [item["answer"] for item in qa_dataset]

# === 5) 编码文本 ===
def encode_corpus(texts):
    texts = [f"为检索生成表示: {t}" for t in texts]
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings

def encode_query(text):
    q = f"为查询生成表示: {text}"
    embedding = model.encode([q], normalize_embeddings=True)
    return embedding

embeddings = encode_corpus(texts)
print("知识块 Embedding shape:", embeddings.shape)

# === 6) 创建 Milvus Collection ===
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=512),
    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=2048),
]
schema = CollectionSchema(fields)
collection = Collection(name=collection_name, schema=schema)

# === 7) 插入数据 ===
collection.insert([embeddings.tolist(), texts])
collection.flush()

# === 8) 创建索引并加载 ===
index_params = {"metric_type": "IP", "index_type": "IVF_FLAT", "params": {"nlist": 64}}
collection.create_index("embedding", index_params)
collection.load()

# === 9) 自动 QA 测试 ===
search_params = {"metric_type": "IP", "params": {"nprobe": 10}}

correct = 0
print("\n=== QA 自动测试结果 ===")

for i, q in enumerate(questions):
    expected = answers[i]
    q_emb = encode_query(q)
    results = collection.search(
        q_emb.tolist(),
        anns_field="embedding",
        param=search_params,
        limit=1,
        output_fields=["content"]
    )
    retrieved = results[0][0].entity.get("content")
    print(f"\nQuestion: {q}")
    print(f"Expected Answer: {expected}")
    print(f"Retrieved Content: {retrieved}")
    if retrieved in texts[i]:
        correct += 1
    else:
        print("❌ Retrieval failed!")

print(f"\n✅ Total QA: {len(questions)}, Correct retrievals: {correct}")

# === 10) 释放资源 ===
collection.release()
