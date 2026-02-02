"""Services module for Fraud Forge backend.

This module contains business logic services for the application.
"""

from app.services.counterfactual_service import (
    CounterfactualService,
    SimilarCaseService,
    build_enhanced_explanation_bundle,
)
from app.services.learning_loop import (
    LearningLoopService,
    create_learning_service,
    RAG_COLLECTIONS,
)
from app.services.multi_collection_rag import (
    MultiCollectionRAGService,
    create_rag_service,
    RAG_COLLECTION_SCHEMA,
)
from app.services.portable_intelligence import (
    PortableIntelligenceService,
    create_portable_service,
    PackageType,
)

__all__ = [
    "CounterfactualService",
    "SimilarCaseService",
    "build_enhanced_explanation_bundle",
    "LearningLoopService",
    "create_learning_service",
    "RAG_COLLECTIONS",
    "MultiCollectionRAGService",
    "create_rag_service",
    "RAG_COLLECTION_SCHEMA",
    "PortableIntelligenceService",
    "create_portable_service",
    "PackageType",
]


