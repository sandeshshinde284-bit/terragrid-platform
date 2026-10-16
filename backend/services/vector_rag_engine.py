"""
RAG Engine Service - Vector-based Historical Learning
Uses Vertex AI embeddings for semantic similarity search
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import numpy as np

logger = logging.getLogger(__name__)

class VectorRAGEngine:
    """
    True RAG (Retrieval-Augmented Generation) Engine
    - Uses Vertex AI embeddings for semantic similarity
    - Stores event embeddings in vector format
    - Retrieves similar historical incidents
    - Returns context injected into Gemini for analysis
    """
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("GCP_REGION", "us-central1")
        self.embedding_model = "text-embedding-004"  # Vertex AI embedding model
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
    
    def get_event_embedding(self, event: Dict[str, Any]) -> Optional[List[float]]:
        """
        Generate embedding for an event using Vertex AI
        
        Args:
            event: Event dict with event_type, location_name, severity, data
            
        Returns:
            List of floats (embedding vector) or None if service unavailable
        """
        if not self.embedding_client:
            return None
        
        try:
            # Create semantic description of the event
            event_type = event.get("event_type", "Unknown")
            location = event.get("location_name", "Unknown")
            severity = event.get("severity", "Unknown")
            impact = event.get("impact", {})
            area = impact.get("affected_area_km2", 0)
            affected_pop = impact.get("affected_population", 0)
            
            # Combine into semantic text for embedding
            semantic_text = f"""
            Disaster Event: {event_type}
            Location: {location}
            Severity: {severity}
            Affected Area: {area} km²
            Population at Risk: {affected_pop:,} people
            """
            
            # Get embedding from Vertex AI
            embeddings = self.embedding_client.get_embeddings([semantic_text])
            
            if embeddings and len(embeddings) > 0:
                embedding_vector = embeddings[0].values
                logger.info(f"VectorRAGEngine: Generated embedding for {event_type} at {location}")
                return embedding_vector
            else:
                logger.warning("VectorRAGEngine: No embedding returned from API")
                return None
                
        except Exception as e:
            logger.error(f"VectorRAGEngine: Error generating embedding ({type(e).__name__}: {e})")
            return None
    
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
    
    def retrieve_similar_incidents(
        self, 
        query_embedding: List[float], 
        db_session,
        event_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar historical incidents using vector similarity
        
        Args:
            query_embedding: Vector embedding of current incident
            db_session: SQLAlchemy session
            event_type: Optional filter by event type
            limit: Number of results to return
            
        Returns:
            List of similar incidents sorted by similarity score
        """
        try:
            from backend.models.event import Event
            
            # Get all historical events (optionally filtered by type)
            query = db_session.query(Event)
            
            if event_type:
                query = query.filter(Event.event_type == event_type)
            
            historical_events = query.order_by(Event.created_at.desc()).limit(100).all()
            
            similar_incidents = []
            
            for event in historical_events:
                # Get embedding for historical event
                event_dict = {
                    "event_type": event.event_type,
                    "location_name": event.location_name,
                    "severity": event.severity,
                    "impact": event.data.get("impact", {}) if event.data else {}
                }
                
                event_embedding = self.get_event_embedding(event_dict)
                
                if not event_embedding:
                    continue
                
                # Calculate similarity
                similarity = self.cosine_similarity(query_embedding, event_embedding)
                
                # Only include if above threshold
                if similarity >= self.similarity_threshold:
                    similar_incidents.append({
                        "id": event.id,
                        "event_type": event.event_type,
                        "location_name": event.location_name,
                        "severity": event.severity,
                        "latitude": event.latitude,
                        "longitude": event.longitude,
                        "created_at": event.created_at,
                        "similarity_score": similarity,
                        "data": event.data
                    })
            
            # Sort by similarity score (descending) and return top N
            similar_incidents.sort(key=lambda x: x["similarity_score"], reverse=True)
            return similar_incidents[:limit]
            
        except Exception as e:
            logger.error(f"VectorRAGEngine: Error retrieving similar incidents ({type(e).__name__}: {e})")
            return []
    
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
    
    def get_historical_context(
        self,
        current_incident: Dict[str, Any],
        db_session,
        limit: int = 5
    ) -> str:
        """
        Main entry point: Get RAG context for an incident
        
        1. Generate embedding for current incident
        2. Retrieve similar incidents via vector similarity
        3. Format as context string for LLM
        
        Returns:
            Context string to inject into Gemini prompt
        """
        location = current_incident.get("location_name", "unknown")
        try:
            # Step 1: Generate query embedding
            query_embedding = self.get_event_embedding(current_incident)
            if not query_embedding:
                logger.info(f"[FEATURE_HEALTH] feature=historical_rag status=fallback location={location} reason=no_embedding")
                return "\n(RAG service unavailable - using fallback)"

            # Step 2: Retrieve similar incidents
            event_type = current_incident.get("event_type")
            similar_incidents = self.retrieve_similar_incidents(
                query_embedding,
                db_session,
                event_type=event_type,
                limit=limit
            )

            # Step 3: Format context
            context = self.format_rag_context(similar_incidents)
            logger.info(f"[FEATURE_HEALTH] feature=historical_rag status=success location={location} similar_incidents={len(similar_incidents)}")
            return context

        except Exception as e:
            logger.error(f"[FEATURE_HEALTH] feature=historical_rag status=error location={location} error={type(e).__name__}: {e}")
            return f"\n(RAG retrieval failed: {str(e)})"
