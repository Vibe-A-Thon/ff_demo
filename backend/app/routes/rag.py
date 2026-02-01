"""RAG document and retrieval routes.

Manage RAG documents and query/retrieval endpoints.
"""

import json
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Depends
from app.core.external_services import DatabaseClient, LLMClient, VectorDocument, VectorStore
from app.core.logging_config import get_logger
from app.audit import record_audit
from app.deps import get_db, get_llm_client, get_vector_store
from app.models import RAGDocument, RAGDocumentCreate, RAGHit, RAGQueryRequest, RAGResponse
from app.rag_utils import (
    build_context_snippets,
    contains_sensitive_identifiers,
    cosine_similarity,
    format_context_prompt,
    get_embedding,
    keyword_score,
    simple_embed,
    tokenize,
)
from app.run_helpers import record_run_event
from app.security import require_permission

router = APIRouter()
logger = get_logger(__name__)

@router.get("/rag/collections")
async def list_rag_collections(
    current_user: dict = Depends(require_permission("rag:read")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, List[str]]:
    """List distinct RAG collections.

    Args:
        current_user: Authorized user context.
        db: Database client.

    Returns:
        Dict[str, List[str]]: Sorted collection names.

    Raises:
        None: No explicit exceptions are raised.
    """
    collections = await db.rag_documents.distinct("collection")
    await record_audit(
        current_user.get("id", "unknown"),
        "rag.collection.list",
        "rag_collection",
        "list",
    )
    return {"collections": sorted(collections)}

@router.get("/rag/documents")
async def list_rag_documents(
    collection: str | None = None,
    limit: int = 50,
    current_user: dict = Depends(require_permission("rag:read")),
    db: DatabaseClient = Depends(get_db),
) -> List[Dict[str, Any]]:
    """List RAG documents.

    Args:
        collection: Optional collection filter.
        limit: Maximum documents to return.
        current_user: Authorized user context.
        db: Database client.

    Returns:
        List[Dict[str, Any]]: Document list.

    Raises:
        None: No explicit exceptions are raised.
    """
    query = {}
    if collection:
        query["collection"] = collection
    docs = await db.rag_documents.find(query, {"_id": 0}).sort("created_at", -1).to_list(max(limit, 1))
    await record_audit(
        current_user.get("id", "unknown"),
        "rag.document.list",
        "rag_document",
        collection or "all",
        metadata={"limit": limit},
    )
    return docs

@router.post("/rag/documents")
async def create_rag_document(
    doc_data: RAGDocumentCreate,
    current_user: dict = Depends(require_permission("rag:write")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
    vector_store: VectorStore = Depends(get_vector_store),
) -> RAGDocument:
    """Create a RAG document with embedding.

    Args:
        doc_data: Document payload.
        current_user: Authorized user context.
        db: Database client.
        llm_client: Optional LLM client.
        vector_store: Vector store client.

    Returns:
        RAGDocument: Created document.

    Raises:
        HTTPException: If sensitive identifiers are detected.
    """
    if doc_data.synthetic_only and contains_sensitive_identifiers(doc_data.content):
        raise HTTPException(status_code=400, detail="Synthetic-only mode: sensitive identifiers detected")
    embedding = await get_embedding(doc_data.content, llm_client=llm_client)
    doc = RAGDocument(**doc_data.model_dump(), embedding=embedding)
    await db.rag_documents.insert_one(doc.model_dump())
    await vector_store.upsert(
        "rag_documents",
        [VectorDocument(id=doc.id, vector=embedding, metadata={"collection": doc.collection, "title": doc.title})],
    )
    await record_audit(
        current_user.get("id", "unknown"),
        "rag.document.created",
        "rag_document",
        doc.id,
        metadata={"collection": doc.collection, "title": doc.title},
    )
    logger.info("rag.document.created", extra={"payload": {"doc_id": doc.id, "collection": doc.collection}})
    return doc

@router.post("/rag/seed")
async def seed_rag_data(
    reset: bool = False,
    current_user: dict = Depends(require_permission("rag:write")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
    vector_store: VectorStore = Depends(get_vector_store),
) -> Dict[str, Any]:
    """Seed RAG collections with taxonomy and defaults.

    Args:
        reset: Whether to clear existing documents.
        current_user: Authorized user context.
        db: Database client.
        llm_client: Optional LLM client.
        vector_store: Vector store client.

    Returns:
        Dict[str, Any]: Seed result.

    Raises:
        None: No explicit exceptions are raised.
    """
    if reset:
        await db.rag_documents.delete_many({})

    taxonomy_path = __import__("pathlib").Path(__file__).resolve().parents[2] / "banking_fraud_taxonomy_catalog_120.json"
    seeded = 0
    if taxonomy_path.exists():
        taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
        if isinstance(taxonomy, list):
            for item in taxonomy:
                title = item.get("name") or item.get("id") or "Taxonomy"
                content = item.get("description") or json.dumps(item, ensure_ascii=False)
                embedding = await get_embedding(content, llm_client=llm_client)
                doc = RAGDocument(
                    collection="taxonomy",
                    title=title,
                    content=content,
                    metadata=item,
                    embedding=embedding,
                )
                await db.rag_documents.insert_one(doc.model_dump())
                await vector_store.upsert(
                    "rag_documents",
                    [VectorDocument(id=doc.id, vector=embedding, metadata={"collection": doc.collection, "title": doc.title})],
                )
                seeded += 1

    defaults = [
        {"collection": "attacks", "title": "Velocity Burst", "content": "Fraudsters split transactions into rapid bursts to evade single-threshold rules.", "metadata": {"team": "red"}},
        {"collection": "patterns", "title": "Account Takeover", "content": "ATO indicators: device mismatch, impossible travel, high-risk beneficiary changes.", "metadata": {"team": "blue"}},
        {"collection": "rules", "title": "VEL-001", "content": "Velocity rule: flag when tx_count > 5 in 10 minutes with shared device signals.", "metadata": {"team": "purple"}},
        {"collection": "explanations", "title": "Decision Template", "content": "Explain outcomes using top signals, rule hits, and confidence statement.", "metadata": {"team": "gold"}},
    ]
    for entry in defaults:
        embedding = await get_embedding(entry["content"], llm_client=llm_client)
        doc = RAGDocument(**entry, embedding=embedding)
        await db.rag_documents.insert_one(doc.model_dump())
        await vector_store.upsert(
            "rag_documents",
            [VectorDocument(id=doc.id, vector=embedding, metadata={"collection": doc.collection, "title": doc.title})],
        )
        seeded += 1

    logger.info("rag.seed.completed", extra={"payload": {"count": seeded, "reset": reset}})
    await record_audit(
        current_user.get("id", "unknown"),
        "rag.seed.completed",
        "rag_collection",
        "seed",
        metadata={"count": seeded, "reset": reset},
    )
    return {"message": "RAG data seeded", "count": seeded}

@router.post("/rag/retrieve")
async def rag_retrieve(
    request: RAGQueryRequest,
    current_user: dict = Depends(require_permission("rag:read")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
) -> List[RAGHit]:
    """Retrieve RAG hits for a query.

    Args:
        request: Retrieval request.
        current_user: Authorized user context.
        db: Database client.
        llm_client: Optional LLM client.

    Returns:
        List[RAGHit]: Ranked hits.

    Raises:
        HTTPException: If sensitive identifiers are detected.
    """
    if request.synthetic_only and contains_sensitive_identifiers(request.query):
        raise HTTPException(status_code=400, detail="Synthetic-only mode: sensitive identifiers detected")
    query = {}
    if request.collections:
        query["collection"] = {"$in": request.collections}
    if request.synthetic_only:
        query["synthetic_only"] = True
    docs = await db.rag_documents.find(query, {"_id": 0}).to_list(500)
    if not docs:
        await record_audit(
            current_user.get("id", "unknown"),
            "rag.retrieve",
            "rag_query",
            request.query[:64],
            metadata={
                "collections": request.collections,
                "top_k": request.top_k,
                "synthetic_only": request.synthetic_only,
                "hits": 0,
            },
        )
        return []

    query_embedding = await get_embedding(request.query, llm_client=llm_client)
    query_tokens = tokenize(request.query)
    scored = []
    for doc in docs:
        doc_embedding = doc.get("embedding") or simple_embed(doc.get("content", ""))
        vector_score = cosine_similarity(query_embedding, doc_embedding)
        keyword_score_value = keyword_score(query_tokens, tokenize(doc.get("content", "")))
        score = vector_score if not request.use_hybrid else (0.7 * vector_score + 0.3 * keyword_score_value)
        scored.append({**doc, "score": score})

    scored.sort(key=lambda d: d.get("score", 0), reverse=True)
    hits = []
    for doc in scored[: request.top_k]:
        snippet = doc.get("content", "")[:180]
        hits.append(
            RAGHit(
                doc_id=doc.get("id"),
                collection=doc.get("collection"),
                title=doc.get("title"),
                score=round(doc.get("score", 0), 4),
                snippet=snippet,
                metadata=doc.get("metadata", {}),
            )
        )
    logger.info(
        "rag.retrieve.completed",
        extra={"payload": {"query": request.query, "collections": request.collections, "hits": len(hits)}},
    )
    await record_audit(
        current_user.get("id", "unknown"),
        "rag.retrieve",
        "rag_query",
        request.query[:64],
        metadata={
            "collections": request.collections,
            "top_k": request.top_k,
            "synthetic_only": request.synthetic_only,
            "hits": len(hits),
        },
    )
    return hits

@router.post("/rag/query")
async def rag_query(
    request: RAGQueryRequest,
    current_user: dict = Depends(require_permission("rag:read")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
) -> RAGResponse:
    """Run RAG query and generate a response.

    Args:
        request: Query request.
        current_user: Authorized user context.
        db: Database client.
        llm_client: Optional LLM client.

    Returns:
        RAGResponse: Query response.

    Raises:
        HTTPException: If sensitive identifiers are detected.
    """
    if request.synthetic_only and contains_sensitive_identifiers(request.query):
        raise HTTPException(status_code=400, detail="Synthetic-only mode: sensitive identifiers detected")

    async def retrieve(with_collections: list[str] | None):
        query = {}
        if with_collections:
            query["collection"] = {"$in": with_collections}
        if request.synthetic_only:
            query["synthetic_only"] = True
        docs = await db.rag_documents.find(query, {"_id": 0}).to_list(500)
        if not docs:
            return []
        query_embedding = await get_embedding(request.query, llm_client=llm_client)
        query_tokens = tokenize(request.query)
        scored_docs = []
        for doc in docs:
            doc_embedding = doc.get("embedding") or simple_embed(doc.get("content", ""))
            vector_score = cosine_similarity(query_embedding, doc_embedding)
            keyword_score_value = keyword_score(query_tokens, tokenize(doc.get("content", "")))
            score = vector_score if not request.use_hybrid else (0.7 * vector_score + 0.3 * keyword_score_value)
            scored_docs.append({**doc, "score": score})
        scored_docs.sort(key=lambda d: d.get("score", 0), reverse=True)
        return scored_docs[: request.top_k]

    used_fallback = False
    scored_docs = await retrieve(request.collections)
    avg_score = sum(doc.get("score", 0) for doc in scored_docs) / max(len(scored_docs), 1)
    if avg_score < request.retrieval_threshold:
        fallback_docs = await retrieve(None)
        if fallback_docs:
            scored_docs = fallback_docs
            used_fallback = True
            avg_score = sum(doc.get("score", 0) for doc in scored_docs) / max(len(scored_docs), 1)

    context_snippets = build_context_snippets(scored_docs, request.max_context_tokens)
    graph_context = []
    if request.include_graph_context:
        query_tokens = tokenize(request.query)
        nodes = await db.knowledge_nodes.find({}, {"_id": 0}).to_list(200)
        for node in nodes:
            text = f"{node.get('name', '')} {json.dumps(node.get('data', {}), default=str)}".lower()
            if any(token in text for token in query_tokens):
                graph_context.append(node)
            if len(graph_context) >= 10:
                break

    answer = ""
    generated_by = "synthetic"
    if llm_client and context_snippets:
        try:
            system_prompt = "You are a fraud defense assistant. Use only the provided context. If context is insufficient, say so. Keep responses synthetic-only and avoid real identifiers."
            prompt = format_context_prompt(context_snippets, request.query)
            answer = await llm_client.chat_completions_create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=400,
            )
            generated_by = "openai"
        except Exception as exc:
            __import__("logging").getLogger(__name__).error(f"RAG generation error: {exc}")

    if not answer:
        if scored_docs:
            bullets = [f"- {doc.get('title') or doc.get('collection')}: {doc.get('content', '')[:160]}" for doc in scored_docs]
            answer = "Summary from retrieved knowledge:\n" + "\n".join(bullets)
        else:
            answer = "No relevant synthetic knowledge found for this query."

    hits = [
        RAGHit(
            doc_id=doc.get("id"),
            collection=doc.get("collection"),
            title=doc.get("title"),
            score=round(doc.get("score", 0), 4),
            snippet=doc.get("content", "")[:180],
            metadata=doc.get("metadata", {}),
        )
        for doc in scored_docs
    ]

    response = RAGResponse(
        query=request.query,
        answer=answer,
        hits=hits,
        context=context_snippets,
        graph_context=graph_context,
        retrieval_score=round(avg_score, 4),
        used_fallback=used_fallback,
        generated_by=generated_by,
    )

    if request.run_id:
        await record_run_event(
            request.run_id,
            "rag.query",
            {"team_id": request.team_id, "query": request.query, "score": response.retrieval_score},
        )

    logger.info(
        "rag.query.completed",
        extra={
            "payload": {
                "query": request.query,
                "hits": len(response.hits),
                "score": response.retrieval_score,
                "used_fallback": response.used_fallback,
                "generated_by": response.generated_by,
            }
        },
    )
    await record_audit(
        current_user.get("id", "unknown"),
        "rag.query",
        "rag_query",
        request.query[:64],
        metadata={
            "collections": request.collections,
            "top_k": request.top_k,
            "synthetic_only": request.synthetic_only,
            "retrieval_score": response.retrieval_score,
            "used_fallback": response.used_fallback,
            "generated_by": response.generated_by,
            "run_id": request.run_id,
            "team_id": request.team_id,
        },
    )
    return response
