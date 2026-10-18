from sqlalchemy import Column, String, Text
from .base import BaseModel


class EmbeddingCache(BaseModel):
    """
    Permanent cache of text embeddings, so the same incident text is embedded once.
    Keyed by a hash of the model name and the exact text that was embedded, so a
    changed text or a changed model gets a fresh embedding automatically.
    """
    __tablename__ = "embedding_cache"

    text_hash = Column(String(64), unique=True, index=True, nullable=False)
    model_name = Column(String(80), nullable=False)
    vector = Column(Text, nullable=False)  # JSON list of floats

    def __repr__(self):
        return f"<EmbeddingCache {self.text_hash[:12]} {self.model_name}>"
