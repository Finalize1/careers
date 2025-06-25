# embedding_module.py

from sentence_transformers import SentenceTransformer

class EmbeddingSingleton:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
        return cls._model

def encode_text(text: str) -> list:
    model = EmbeddingSingleton.get_model()
    vec = model.encode([text], normalize_embeddings=True)
    return vec[0]
