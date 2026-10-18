"""
RAG Engine Service - Vector-based Historical Learning
Uses Vertex AI embeddings for semantic similarity search.

Embeddings are cached in PostgreSQL (embedding_cache) by a hash of the model and
the exact text. Texts that are not cached are sent in batches, so one report makes
a few embedding requests instead of one per past incident. When embedding is
unavailable, the context says so; it never reports "no matches" for that case.
"""

import os
import json
import hashlib
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-004"  # Vertex AI embedding model
BATCH_SIZE = 50          # texts per embedding request
RETRY_WAITS = (2, 4)     # seconds to wait after a quota error, before retrying
CANDIDATE_LIMIT = 100    # past incidents compared per report


class VectorRAGEngine:
    """
    True RAG (Retrieval-Augmented Generation) Engine
    - Uses Vertex AI embeddings for semantic similarity
    - Caches embeddings in PostgreSQL so each text is embedded once
    - Retrieves similar historical incidents
    - Returns context injected into Gemini for analysis
    """

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("GCP_REGION", "us-central1")
        self.embedding_model = EMBEDDING_MODEL
        self.similarity_threshold = 0.6  # Cosine similarity threshold

        try:
            from vertexai.language_models import TextEmbeddingModel
            import vertexai

            if self.project_id:
                vertexai.init(project=self.project_id, location=self.location)
                self.embedding_client = TextEmbeddingModel.from_pretrained(self.embedding_model)
                logger.info("VectorRAGEngine: Vertex AI Text Embeddings initialized successfully.")
            else:
                logger.warning("VectorRAGEngine: GCP_PROJECT_ID not configured. Will use fallback.")
                self.embedding_client = None

        except Exception as e:
            logger.warning(f"VectorRAGEngine: Could not initialize embeddings ({type(e).__name__}: {e}). Will use fallback.")
            self.embedding_client = None

    # ------------------------------------------------------------------
    # Text and cache keys
    # ------------------------------------------------------------------

    @staticmethod
    def semantic_text(event: Dict[str, Any]) -> str:
        """The text that is embedded for an incident. Changing it changes the cache key."""
        event_type = event.get("event_type") or "Unknown"
        location = event.get("location_name") or "Unknown"
        severity = event.get("severity") or "Unknown"
        impact = event.get("impact") or {}
        area = impact.get("affected_area_km2") or 0
        affected_pop = impact.get("affected_population") or 0
        text = (
            f"Disaster Event: {event_type} "
            f"Location: {location} "
            f"Severity: {severity} "
            f"Affected Area: {area} km2 "
            f"Population at Risk: {affected_pop:,} people"
        )
        return " ".join(text.split())

    @staticmethod
    def text_hash(model: str, text: str) -> str:
        return hashlib.sha256(f"{model}\n{text}".encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # Embedding with cache
    # ------------------------------------------------------------------

    def _cached_vectors(self, db_session, hashes: List[str]) -> Dict[str, List[float]]:
        if db_session is None or not hashes:
            return {}
        from backend.models.embedding_cache import EmbeddingCache
        rows = db_session.query(EmbeddingCache).filter(EmbeddingCache.text_hash.in_(hashes)).all()
        return {row.text_hash: json.loads(row.vector) for row in rows}

    def _embed_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """One embedding request. Retries briefly on quota errors. None if it still fails."""
        if not self.embedding_client:
            return None
        for attempt in range(len(RETRY_WAITS) + 1):
            try:
                results = self.embedding_client.get_embeddings(texts)
                return [item.values for item in results]
            except Exception as e:
                is_quota = type(e).__name__ == "ResourceExhausted" or "429" in str(e)
                if is_quota and attempt < len(RETRY_WAITS):
                    time.sleep(RETRY_WAITS[attempt])
                    continue
                logger.error(f"VectorRAGEngine: embedding request failed ({type(e).__name__}: {e})")
                return None
        return None

    def _store(self, db_session, vectors_by_hash: Dict[str, List[float]]) -> None:
        if db_session is None or not vectors_by_hash:
            return
        try:
            from backend.models.embedding_cache import EmbeddingCache
            already = self._cached_vectors(db_session, list(vectors_by_hash))
            for text_hash, vector in vectors_by_hash.items():
                if text_hash in already:
                    continue
                db_session.add(EmbeddingCache(
                    text_hash=text_hash,
                    model_name=self.embedding_model,
                    vector=json.dumps(vector),
                ))
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            logger.warning(f"VectorRAGEngine: could not store embeddings in cache ({type(e).__name__}: {e})")

    def embed_texts(self, texts: List[str], db_session=None) -> Tuple[List[Optional[List[float]]], int]:
        """
        Vectors aligned with `texts`. An entry is None when it could not be embedded.
        Returns (vectors, number_unavailable).
        """
        normalized = [" ".join(t.split()) for t in texts]
        hashes = [self.text_hash(self.embedding_model, t) for t in normalized]

        cached = self._cached_vectors(db_session, list(set(hashes)))

        missing: Dict[str, str] = {}
        for text_hash, text in zip(hashes, normalized):
            if text_hash not in cached and text_hash not in missing:
                missing[text_hash] = text

        fresh: Dict[str, List[float]] = {}
        pending = list(missing.items())
        for start in range(0, len(pending), BATCH_SIZE):
            chunk = pending[start:start + BATCH_SIZE]
            vectors = self._embed_batch([text for _, text in chunk])
            if vectors is None or len(vectors) != len(chunk):
                continue
            for (text_hash, _), vector in zip(chunk, vectors):
                fresh[text_hash] = vector

        self._store(db_session, fresh)

        out: List[Optional[List[float]]] = []
        for text_hash in hashes:
            out.append(cached.get(text_hash) or fresh.get(text_hash))
        unavailable = sum(1 for v in out if v is None)
        return out, unavailable

    def get_event_embedding(self, event: Dict[str, Any], db_session=None) -> Optional[List[float]]:
        """Embedding for one incident, or None if it is unavailable."""
        vectors, _ = self.embed_texts([self.semantic_text(event)], db_session)
        return vectors[0]

    # ------------------------------------------------------------------
    # Similarity
    # ------------------------------------------------------------------

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        Range: 0 to 1 (1 = identical, 0 = orthogonal)
        """
        try:
            arr1 = np.array(vec1)
            arr2 = np.array(vec2)

            dot_product = np.dot(arr1, arr2)
            norm1 = np.linalg.norm(arr1)
            norm2 = np.linalg.norm(arr2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return float(similarity)

        except Exception as e:
            logger.error(f"VectorRAGEngine: Cosine similarity error ({type(e).__name__}: {e})")
            return 0.0

    def format_rag_context(self, similar_incidents: List[Dict[str, Any]]) -> str:
        """
        Format retrieved incidents into context for LLM injection
        """
        if not similar_incidents:
            return "\nNo similar historical incidents found in database."

        context = "\n\nHISTORICAL CONTEXT (Vector-RAG Retrieved):"
        context += f"\n{len(similar_incidents)} similar incidents found:\n"

        for i, incident in enumerate(similar_incidents, 1):
            context += f"\n{i}. {incident['event_type']} at {incident['location_name']}"
            context += f"\n   Severity: {incident['severity']} | Similarity: {incident['similarity_score']:.2%}"
            context += f"\n   Location: ({incident['latitude']:.2f}, {incident['longitude']:.2f})"
            context += f"\n   Date: {incident['created_at']}"

        return context

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def get_historical_context(
        self,
        current_incident: Dict[str, Any],
        db_session,
        limit: int = 5
    ) -> str:
        """
        Main entry point: Get RAG context for an incident

        1. Embed the current incident and the recent past incidents (cached, batched)
        2. Rank past incidents by similarity
        3. Format as context string for LLM. If embedding was unavailable, say so.

        Returns:
            Context string to inject into Gemini prompt
        """
        location = current_incident.get("location_name", "unknown")
        try:
            from backend.models.event import Event

            event_type = current_incident.get("event_type")
            query = db_session.query(Event)
            if event_type:
                query = query.filter(Event.event_type == event_type)
            past_events = query.order_by(Event.created_at.desc()).limit(CANDIDATE_LIMIT).all()

            past_dicts = [
                {
                    "event_type": e.event_type,
                    "location_name": e.location_name,
                    "severity": e.severity,
                    "impact": (e.data or {}).get("impact", {}) if e.data else {},
                }
                for e in past_events
            ]

            texts = [self.semantic_text(current_incident)] + [self.semantic_text(d) for d in past_dicts]
            vectors, _ = self.embed_texts(texts, db_session)

            query_vector = vectors[0]
            if query_vector is None:
                logger.info(f"[FEATURE_HEALTH] feature=historical_rag status=fallback location={location} reason=embedding_unavailable")
                return (
                    "\nUNAVAILABLE: the embedding service did not respond, so past incidents were not compared "
                    "for this report. Do not treat this as 'no history'."
                )

            similar_incidents = []
            for past, vector in zip(past_events, vectors[1:]):
                if vector is None:
                    continue
                similarity = self.cosine_similarity(query_vector, vector)
                if similarity >= self.similarity_threshold:
                    similar_incidents.append({
                        "id": past.id,
                        "event_type": past.event_type,
                        "location_name": past.location_name,
                        "severity": past.severity,
                        "latitude": past.latitude,
                        "longitude": past.longitude,
                        "created_at": past.created_at,
                        "similarity_score": similarity,
                        "data": past.data,
                    })

            similar_incidents.sort(key=lambda x: x["similarity_score"], reverse=True)
            top = similar_incidents[:limit]
            context = self.format_rag_context(top)

            skipped = sum(1 for v in vectors[1:] if v is None)
            if skipped:
                context += (
                    f"\n{skipped} of {len(past_events)} past incidents could not be compared "
                    f"(embedding service unavailable). Matches may be incomplete."
                )

            logger.info(
                f"[FEATURE_HEALTH] feature=historical_rag status=success location={location} "
                f"similar_incidents={len(top)} compared={len(past_events) - skipped} skipped={skipped}"
            )
            return context

        except Exception as e:
            logger.error(f"[FEATURE_HEALTH] feature=historical_rag status=error location={location} error={type(e).__name__}: {e}")
            return f"\n(RAG retrieval failed: {str(e)})"
