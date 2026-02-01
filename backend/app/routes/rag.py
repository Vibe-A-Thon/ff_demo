"""RAG document and retrieval routes.

Manage RAG documents and query/retrieval endpoints.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from app.core.external_services import DatabaseClient, LLMClient, VectorDocument, VectorStore
from app.core.logging_config import get_logger
from app.config import get_integration_setting
from app.audit import record_audit
from app.deps import get_db, get_llm_client, get_vector_store
from app.models import (
    RAGDocument,
    RAGDocumentCreate,
    RAGHit,
    RAGMediaDocument,
    RAGQueryRequest,
    RAGResponse,
    RAGEvaluationRequest,
    RAGEvaluationReport,
)
from app.agentic_rag import plan_agentic_steps, run_agentic_steps
from app.rag_ingest import OCRUnavailableError, extract_text_from_upload
from app.multimodal_embeddings import embed_image_bytes
from app.rag_cache import cag_cache, get_persisted_cache, set_persisted_cache, hash_cache_key
from app.rag_graph import graph_retrieve
from app.graph_rag_neo4j import neo4j_graph_retrieve
from app.rag_utils import (
    build_context_snippets,
    build_graph_snippets,
    contains_sensitive_identifiers,
    cosine_similarity,
    compute_groundedness_metrics,
    format_context_prompt,
    get_embedding,
    keyword_score,
    detect_contradictions,
    deduplicate_hits,
    expand_query,
    refine_query_with_feedback,
    rerank_hits,
    rewrite_query,
    simple_embed,
    select_rag_mode,
    tokenize,
    verify_answer_with_context,
)
from app.rag_reranker import classify_contradictions, rerank_hits_strong
from app.run_helpers import record_run_event
from app.security import require_permission

router = APIRouter()
logger = get_logger(__name__)


async def _record_cache_telemetry(
    db: DatabaseClient,
    event: str,
    layer: str,
    key_hash: str,
    metadata: Dict[str, Any] | None = None,
) -> None:
    await db.rag_cache_telemetry.insert_one(
        {
            "event": event,
            "layer": layer,
            "key_hash": key_hash,
            "metadata": metadata or {},
            "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        }
    )


async def _retrieve_scored_docs(
    query_text: str,
    collections: list[str] | None,
    synthetic_only: bool,
    use_hybrid: bool,
    top_k: int,
    db: DatabaseClient,
    llm_client: LLMClient | None,
    current_role: str | None,
) -> List[Dict[str, Any]]:
    query = {}
    if collections:
        query["collection"] = {"$in": collections}
    if synthetic_only:
        query["synthetic_only"] = True
    docs = await db.rag_documents.find(query, {"_id": 0}).to_list(500)
    if not docs:
        return []
    query_embedding = await get_embedding(query_text, llm_client=llm_client)
    query_tokens = tokenize(query_text)
    scored_docs = []
    for doc in docs:
        allowed_roles = doc.get("allowed_roles") or doc.get("metadata", {}).get("allowed_roles")
        if allowed_roles and current_role not in allowed_roles:
            continue
        doc_embedding = doc.get("embedding") or simple_embed(doc.get("content", ""))
        vector_score = cosine_similarity(query_embedding, doc_embedding)
        keyword_score_value = keyword_score(query_tokens, tokenize(doc.get("content", "")))
        score = vector_score if not use_hybrid else (0.7 * vector_score + 0.3 * keyword_score_value)
        scored_docs.append({**doc, "score": score})
    scored_docs.sort(key=lambda d: d.get("score", 0), reverse=True)
    return scored_docs[: max(top_k, 1)]


async def _graph_context(
    query_text: str,
    db: DatabaseClient,
    top_k: int,
    graph_hops: int,
) -> List[Dict[str, Any]]:
    try:
        neo4j_hits = await neo4j_graph_retrieve(query_text, top_k=top_k, max_hops=graph_hops)
        if neo4j_hits:
            return neo4j_hits
    except Exception as exc:
        logging.getLogger(__name__).warning("neo4j_graph_retrieve_failed", extra={"payload": {"error": str(exc)}})
    nodes = await db.knowledge_nodes.find({}, {"_id": 0}).to_list(500)
    return graph_retrieve(query_text, nodes, top_k=top_k, max_hops=graph_hops)

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
    role = current_user.get("role")
    filtered = []
    for doc in docs:
        allowed_roles = doc.get("allowed_roles") or doc.get("metadata", {}).get("allowed_roles")
        if allowed_roles and role not in allowed_roles:
            continue
        filtered.append(doc)
    await record_audit(
        current_user.get("id", "unknown"),
        "rag.document.list",
        "rag_document",
        collection or "all",
        metadata={"limit": limit},
    )
    return filtered

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


@router.post("/rag/ingest-file")
async def ingest_rag_file(
    file: UploadFile = File(...),
    collection: str = Form(...),
    title: str | None = Form(None),
    metadata: str | None = Form(None),
    allowed_roles: str | None = Form(None),
    synthetic_only: bool = Form(True),
    current_user: dict = Depends(require_permission("rag:write")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
    vector_store: VectorStore = Depends(get_vector_store),
) -> RAGDocument:
    """Ingest a PDF or image file into the RAG corpus using OCR.

    Args:
        file: Uploaded file.
        collection: Collection name.
        title: Optional title override.
        metadata: Optional JSON metadata string.
        synthetic_only: Synthetic-only guardrail.

    Returns:
        RAGDocument: Created document.
    """
    raw = await file.read()
    try:
        extracted_text, file_meta = extract_text_from_upload(file.filename or "upload", file.content_type or "", raw)
    except OCRUnavailableError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not extracted_text:
        raise HTTPException(status_code=400, detail="No text extracted from file")
    if synthetic_only and contains_sensitive_identifiers(extracted_text):
        raise HTTPException(status_code=400, detail="Synthetic-only mode: sensitive identifiers detected")

    parsed_metadata: Dict[str, Any] = {}
    if metadata:
        try:
            parsed_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid metadata JSON")
    parsed_allowed_roles = None
    if allowed_roles:
        try:
            parsed_allowed_roles = json.loads(allowed_roles)
            if not isinstance(parsed_allowed_roles, list):
                raise ValueError("allowed_roles must be a list")
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid allowed_roles JSON") from exc
    parsed_metadata.update(file_meta)

    embedding = await get_embedding(extracted_text, llm_client=llm_client)
    doc = RAGDocument(
        collection=collection,
        title=title or file.filename,
        content=extracted_text,
        metadata=parsed_metadata,
        embedding=embedding,
        synthetic_only=synthetic_only,
        allowed_roles=parsed_allowed_roles,
    )
    await db.rag_documents.insert_one(doc.model_dump())
    await vector_store.upsert(
        "rag_documents",
        [VectorDocument(id=doc.id, vector=embedding, metadata={"collection": doc.collection, "title": doc.title})],
    )
    await record_audit(
        current_user.get("id", "unknown"),
        "rag.document.ingested",
        "rag_document",
        doc.id,
        metadata={"collection": doc.collection, "title": doc.title, "source": parsed_metadata.get("source")},
    )
    logger.info("rag.document.ingested", extra={"payload": {"doc_id": doc.id, "collection": doc.collection}})
    return doc


@router.post("/rag/ingest-media")
async def ingest_rag_media(
    file: UploadFile = File(...),
    collection: str = Form(...),
    title: str | None = Form(None),
    metadata: str | None = Form(None),
    allowed_roles: str | None = Form(None),
    synthetic_only: bool = Form(True),
    current_user: dict = Depends(require_permission("rag:write")),
    db: DatabaseClient = Depends(get_db),
    vector_store: VectorStore = Depends(get_vector_store),
) -> RAGMediaDocument:
    """Ingest an image for multimodal embeddings."""
    raw = await file.read()
    if synthetic_only and contains_sensitive_identifiers(file.filename or ""):
        raise HTTPException(status_code=400, detail="Synthetic-only mode: sensitive identifiers detected")

    parsed_metadata: Dict[str, Any] = {}
    if metadata:
        try:
            parsed_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid metadata JSON")
    parsed_allowed_roles = None
    if allowed_roles:
        try:
            parsed_allowed_roles = json.loads(allowed_roles)
            if not isinstance(parsed_allowed_roles, list):
                raise ValueError("allowed_roles must be a list")
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid allowed_roles JSON") from exc

    try:
        embedding = await embed_image_bytes(raw)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    media_doc = RAGMediaDocument(
        collection=collection,
        title=title or file.filename,
        media_type=file.content_type or "image",
        metadata=parsed_metadata,
        allowed_roles=parsed_allowed_roles,
        embedding=embedding,
        synthetic_only=synthetic_only,
    )
    await db.rag_media_documents.insert_one(media_doc.model_dump())
    await vector_store.upsert(
        "rag_media",
        [
            VectorDocument(
                id=media_doc.id,
                vector=embedding,
                metadata={
                    "collection": media_doc.collection,
                    "title": media_doc.title,
                    "media_type": media_doc.media_type,
                    "allowed_roles": media_doc.allowed_roles,
                },
            )
        ],
    )
    await record_audit(
        current_user.get("id", "unknown"),
        "rag.media.ingested",
        "rag_media",
        media_doc.id,
        metadata={"collection": media_doc.collection, "title": media_doc.title},
    )
    logger.info("rag.media.ingested", extra={"payload": {"doc_id": media_doc.id, "collection": media_doc.collection}})
    return media_doc


@router.post("/rag/retrieve-media")
async def retrieve_rag_media(
    file: UploadFile = File(...),
    collection: str | None = Form(None),
    top_k: int = Form(5),
    current_user: dict = Depends(require_permission("rag:read")),
    db: DatabaseClient = Depends(get_db),
    vector_store: VectorStore = Depends(get_vector_store),
) -> List[RAGHit]:
    """Retrieve similar media using image embeddings."""
    raw = await file.read()
    try:
        embedding = await embed_image_bytes(raw)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    matches = await vector_store.query("rag_media", embedding, top_k=top_k)
    hits: List[RAGHit] = []
    role = current_user.get("role")
    for match in matches:
        meta = match.metadata or {}
        allowed_roles = meta.get("allowed_roles")
        if allowed_roles and role not in allowed_roles:
            continue
        if collection and meta.get("collection") != collection:
            continue
        hits.append(
            RAGHit(
                doc_id=match.id,
                collection=meta.get("collection", "media"),
                title=meta.get("title"),
                score=round(match.score, 4),
                snippet=meta.get("media_type", "image"),
                metadata=meta,
            )
        )

    await db.rag_retrieval_logs.insert_one(
        {
            "event": "rag.media.retrieve",
            "collection": collection,
            "top_k": top_k,
            "user_id": current_user.get("id"),
            "user_role": role,
            "hits": [
                {
                    "doc_id": hit.doc_id,
                    "collection": hit.collection,
                    "score": hit.score,
                }
                for hit in hits
            ],
            "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        }
    )
    return hits

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
    scored = await _retrieve_scored_docs(
        request.query,
        request.collections,
        request.synthetic_only,
        request.use_hybrid,
        request.top_k,
        db,
        llm_client,
        current_user.get("role"),
    )
    if not scored:
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

    avg_score = sum(doc.get("score", 0) for doc in scored) / max(len(scored), 1)
    if request.enable_crag or request.rag_mode.lower() == "crag":
        if avg_score < request.retrieval_threshold:
            scored = await _retrieve_scored_docs(
                request.query,
                None,
                request.synthetic_only,
                request.use_hybrid,
                request.top_k,
                db,
                llm_client,
                current_user.get("role"),
            )

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
    await db.rag_retrieval_logs.insert_one(
        {
            "event": "rag.retrieve",
            "query": request.query,
            "collections": request.collections,
            "top_k": request.top_k,
            "synthetic_only": request.synthetic_only,
            "use_hybrid": request.use_hybrid,
            "user_id": current_user.get("id"),
            "user_role": current_user.get("role"),
            "hits": [
                {
                    "doc_id": hit.doc_id,
                    "collection": hit.collection,
                    "score": hit.score,
                }
                for hit in hits
            ],
            "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        }
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

    required_llm_modes = {"advanced", "advanced-rag", "self-rag", "self_rag", "agentic"}
    if request.rag_mode and request.rag_mode.lower() in required_llm_modes and llm_client is None:
        raise HTTPException(status_code=400, detail="LLM client not configured. Set OPENAI_API_KEY in .env")

    rag_mode = select_rag_mode(request.query, request.rag_mode)
    used_fallback = False
    corrections: List[str] = []
    scored_docs: List[Dict[str, Any]] = []
    avg_score = 0.0
    effective_query = request.query
    agentic_trace: List[Dict[str, Any]] = []

    if rag_mode in {"advanced", "advanced-rag"}:
        rewritten = await rewrite_query(effective_query, llm_client)
        expanded = await expand_query(rewritten, llm_client)
        if expanded != effective_query:
            corrections.append("query_rewrite_expand")
            effective_query = expanded

    cache_key = json.dumps(
        {
            "query": request.query,
            "collections": request.collections,
            "synthetic_only": request.synthetic_only,
            "use_hybrid": request.use_hybrid,
            "include_graph_context": request.include_graph_context,
            "graph_hops": request.graph_hops,
            "top_k": request.top_k,
        },
        sort_keys=True,
    )
    cache_key_hash = hash_cache_key(cache_key)
    cached_payload = None
    cache_layer = "none"
    if rag_mode == "cag":
        cached_payload = await get_persisted_cache(db, cache_key)
        if cached_payload:
            cache_layer = "persisted"
        if not cached_payload:
            cached_payload = cag_cache.get(cache_key)
            if cached_payload:
                cache_layer = "memory"
        if cached_payload:
            corrections.append("cache_hit")
            scored_docs = cached_payload.get("scored_docs", [])
            avg_score = float(cached_payload.get("avg_score", 0.0))
            await _record_cache_telemetry(
                db,
                "hit",
                cache_layer,
                cache_key_hash,
                {"rag_mode": rag_mode},
            )
        else:
            await _record_cache_telemetry(
                db,
                "miss",
                "none",
                cache_key_hash,
                {"rag_mode": rag_mode},
            )

    if rag_mode == "agentic":
        steps = await plan_agentic_steps(effective_query, llm_client)
        agentic_result = await run_agentic_steps(
            steps,
            db,
            llm_client,
            _retrieve_scored_docs,
            _graph_context,
            current_user.get("role"),
            request.synthetic_only,
            request.use_hybrid,
            request.top_k,
        )
        scored_docs = agentic_result.get("hits", [])
        graph_context = agentic_result.get("graph_hits", [])
        agentic_trace = agentic_result.get("trace", [])
        avg_score = sum(doc.get("score", 0) for doc in scored_docs) / max(len(scored_docs), 1)
        corrections.append("agentic_planner")
    elif rag_mode != "graph" and not cached_payload:
        scored_docs = await _retrieve_scored_docs(
            effective_query,
            request.collections,
            request.synthetic_only,
            request.use_hybrid,
            request.top_k,
            db,
            llm_client,
            current_user.get("role"),
        )
        avg_score = sum(doc.get("score", 0) for doc in scored_docs) / max(len(scored_docs), 1)

    if rag_mode in {"advanced", "advanced-rag"} and scored_docs:
        scored_docs = rerank_hits_strong(effective_query, scored_docs)
        scored_docs = rerank_hits(effective_query, scored_docs)
        scored_docs = deduplicate_hits(scored_docs)
        contradictions = classify_contradictions(effective_query, scored_docs)
        if not contradictions:
            contradictions = detect_contradictions(scored_docs)
        if contradictions:
            corrections.append("contradiction_flagged")

    if avg_score < request.retrieval_threshold and (request.enable_crag or rag_mode == "crag"):
        corrections.append("broaden_collections")
        fallback_docs = await _retrieve_scored_docs(
            request.query,
            None,
            request.synthetic_only,
            request.use_hybrid,
            request.top_k,
            db,
            llm_client,
            current_user.get("role"),
        )
        fallback_score = sum(doc.get("score", 0) for doc in fallback_docs) / max(len(fallback_docs), 1)
        if fallback_docs and fallback_score >= avg_score:
            scored_docs = fallback_docs
            used_fallback = True
            avg_score = fallback_score

        if avg_score < request.retrieval_threshold:
            corrections.append("rewrite_query")
            rewritten_query = await refine_query_with_feedback(
                request.query,
                "low_retrieval_score",
                llm_client,
            )
            if rewritten_query and rewritten_query != request.query:
                rewritten_docs = await _retrieve_scored_docs(
                    rewritten_query,
                    request.collections,
                    request.synthetic_only,
                    request.use_hybrid,
                    request.top_k,
                    db,
                    llm_client,
                    current_user.get("role"),
                )
                rewritten_score = sum(doc.get("score", 0) for doc in rewritten_docs) / max(len(rewritten_docs), 1)
                if rewritten_docs and rewritten_score >= avg_score:
                    scored_docs = rewritten_docs
                    avg_score = rewritten_score

    if cached_payload:
        context_snippets = cached_payload.get("context_snippets", [])
    else:
        context_snippets = build_context_snippets(scored_docs, request.max_context_tokens)
    if not graph_context:
        graph_context = []
    if (request.include_graph_context or rag_mode in {"graph", "crag", "self-rag", "self_rag"}) and not graph_context:
        if cached_payload:
            graph_context = cached_payload.get("graph_context", [])
        else:
            graph_context = await _graph_context(
                request.query,
                db,
                request.top_k,
                request.graph_hops,
            )
        if graph_context and rag_mode == "crag" and avg_score < request.retrieval_threshold:
            corrections.append("graph_context")
        if not graph_context and rag_mode == "crag" and avg_score < request.retrieval_threshold:
            corrections.append("switch_to_graph")

    graph_score = 0.0
    if graph_context:
        graph_score = max((hit.get("score", 0) for hit in graph_context), default=0.0)
    if rag_mode == "graph" and graph_score > avg_score:
        avg_score = graph_score
    if rag_mode == "crag" and avg_score < request.retrieval_threshold and graph_score > 0:
        corrections.append("graph_boost")
        avg_score = max(avg_score, graph_score)

    graph_snippets = build_graph_snippets(graph_context) if graph_context else []

    answer = ""
    generated_by = "synthetic"
    verification_score = 0.0
    verification_passed = False
    max_attempts = 3 if rag_mode in {"self-rag", "self_rag"} else 1

    for attempt in range(max_attempts):
        combined_context = context_snippets + graph_snippets
        if llm_client and combined_context:
            try:
                system_prompt = "You are a fraud defense assistant. Use only the provided context. If context is insufficient, say so. Keep responses synthetic-only and avoid real identifiers."
                prompt = format_context_prompt(combined_context, effective_query)
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

        if rag_mode in {"self-rag", "self_rag"}:
            verification_score, feedback = await verify_answer_with_context(answer, combined_context, llm_client)
            verification_passed = verification_score >= 0.7
            if verification_passed:
                break
            corrections.append("self_rag_retry")
            if attempt == 0:
                fallback_docs = await _retrieve_scored_docs(
                    effective_query,
                    None,
                    request.synthetic_only,
                    request.use_hybrid,
                    request.top_k,
                    db,
                    llm_client,
                    current_user.get("role"),
                )
                if fallback_docs:
                    scored_docs = fallback_docs
                    used_fallback = True
                    context_snippets = build_context_snippets(scored_docs, request.max_context_tokens)
            if attempt == 1:
                effective_query = await refine_query_with_feedback(effective_query, feedback, llm_client)
        else:
            break

    if not answer:
        if scored_docs:
            bullets = [f"- {doc.get('title') or doc.get('collection')}: {doc.get('content', '')[:160]}" for doc in scored_docs]
            answer = "Summary from retrieved knowledge:\n" + "\n".join(bullets)
        elif graph_context:
            bullets = []
            for hit in graph_context:
                node = hit.get("node", {})
                name = node.get("name", "node")
                neighbors = hit.get("neighbors", [])
                neighbor_names = ", ".join(n.get("name", "") for n in neighbors[:4])
                if neighbor_names:
                    bullets.append(f"- {name} connected to {neighbor_names}")
                else:
                    bullets.append(f"- {name}")
            answer = "Graph context summary:\n" + "\n".join(bullets)
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

    if rag_mode == "cag" and not cached_payload:
        payload = {
            "scored_docs": scored_docs,
            "context_snippets": context_snippets,
            "graph_context": graph_context,
            "avg_score": avg_score,
        }
        cag_cache.set(cache_key, payload)
        await set_persisted_cache(db, cache_key, payload)
        await _record_cache_telemetry(
            db,
            "set",
            "persisted",
            cache_key_hash,
            {"rag_mode": rag_mode, "items": len(scored_docs)},
        )

    response = RAGResponse(
        query=request.query,
        answer=answer,
        hits=hits,
        context=context_snippets,
        graph_context=graph_context,
        retrieval_score=round(avg_score, 4),
        used_fallback=used_fallback,
        generated_by=generated_by,
        rag_mode_used=rag_mode,
        corrections=corrections,
        verification_score=round(verification_score, 4),
        verification_passed=verification_passed,
        agentic_trace=agentic_trace,
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
            "rag_mode": response.rag_mode_used,
            "corrections": response.corrections,
        },
    )
    await db.rag_retrieval_logs.insert_one(
        {
            "event": "rag.query",
            "query": request.query,
            "collections": request.collections,
            "top_k": request.top_k,
            "synthetic_only": request.synthetic_only,
            "use_hybrid": request.use_hybrid,
            "rag_mode": response.rag_mode_used,
            "corrections": response.corrections,
            "retrieval_score": response.retrieval_score,
            "verification_score": response.verification_score,
            "verification_passed": response.verification_passed,
            "used_fallback": response.used_fallback,
            "user_id": current_user.get("id"),
            "user_role": current_user.get("role"),
            "hits": [
                {
                    "doc_id": hit.doc_id,
                    "collection": hit.collection,
                    "score": hit.score,
                }
                for hit in response.hits
            ],
            "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        }
    )
    return response


@router.post("/rag/evaluate")
async def evaluate_rag(
    request: RAGEvaluationRequest,
    current_user: dict = Depends(require_permission("rag:read")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
) -> RAGEvaluationReport:
    """Evaluate RAG retrieval quality on a set of synthetic queries.

    Args:
        request: Evaluation request payload.
        current_user: Authorized user context.
        db: Database client.
        llm_client: Optional LLM client.

    Returns:
        RAGEvaluationReport: Evaluation report.

    Raises:
        HTTPException: If no cases are provided.
    """
    if not request.cases:
        raise HTTPException(status_code=400, detail="No evaluation cases provided")

    per_case: List[Dict[str, Any]] = []
    precision_scores: List[float] = []
    recall_scores: List[float] = []
    collection_hits: List[int] = []
    keyword_coverages: List[float] = []
    faithfulness_scores: List[float] = []
    answer_relevancy_scores: List[float] = []

    rag_mode = (request.rag_mode or "hybrid").lower()

    for case in request.cases:
        scored_docs: List[Dict[str, Any]] = []
        if rag_mode != "graph":
            scored_docs = await _retrieve_scored_docs(
                case.query,
                None,
                case.synthetic_only,
                request.use_hybrid,
                request.top_k,
                db,
                llm_client,
                current_user.get("role"),
            )
        graph_context = []
        if request.include_graph_context or rag_mode in {"graph", "crag"}:
            graph_context = await _graph_context(
                case.query,
                db,
                request.top_k,
                request.graph_hops,
            )
        hits = [
            RAGHit(
                doc_id=doc.get("id"),
                collection=doc.get("collection"),
                title=doc.get("title"),
                score=round(doc.get("score", 0), 4),
                snippet=doc.get("content", "")[:180],
                metadata=doc.get("metadata", {}),
            )
            for doc in scored_docs[: request.top_k]
        ]

        context_snippets = build_context_snippets(scored_docs, 800)
        generated_answer = case.reference_answer or ""
        if not generated_answer:
            if llm_client and context_snippets:
                try:
                    system_prompt = "You are a fraud defense assistant. Use only the provided context."
                    prompt = format_context_prompt(context_snippets, case.query)
                    generated_answer = await llm_client.chat_completions_create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        max_tokens=200,
                    )
                except Exception:
                    generated_answer = ""
            if not generated_answer and scored_docs:
                bullets = [doc.get("content", "")[:140] for doc in scored_docs[:3]]
                generated_answer = " ".join(bullets)

        grounded = await compute_groundedness_metrics(
            case.query,
            generated_answer,
            context_snippets,
            llm_client,
        )

        expected_collections = set(case.expected_collections or [])
        expected_doc_ids = set(case.expected_doc_ids or [])
        expected_keywords = [kw.lower() for kw in (case.expected_keywords or [])]

        relevant_hits = 0
        if expected_collections or expected_doc_ids:
            for hit in hits:
                if hit.doc_id in expected_doc_ids or hit.collection in expected_collections:
                    relevant_hits += 1

        precision = relevant_hits / max(len(hits), 1)
        recall = None
        if expected_doc_ids:
            recall = relevant_hits / max(len(expected_doc_ids), 1)
        elif expected_collections:
            recall = 1.0 if relevant_hits > 0 else 0.0

        keyword_coverage = None
        if expected_keywords:
            joined = " ".join(doc.get("content", "").lower() for doc in scored_docs[: request.top_k])
            graph_joined = " ".join(
                f"{hit.get('node', {}).get('name', '')} {json.dumps(hit.get('node', {}).get('data', {}), default=str)}".lower()
                for hit in graph_context
            )
            combined = f"{joined} {graph_joined}".strip()
            matched = sum(1 for kw in expected_keywords if kw in combined)
            keyword_coverage = matched / max(len(expected_keywords), 1)

        case_payload = {
            "query": case.query,
            "hits": [hit.model_dump() for hit in hits],
            "graph_hits": graph_context,
            "precision_at_k": round(precision, 4),
            "recall_at_k": round(recall, 4) if recall is not None else None,
            "collection_hit": relevant_hits > 0 if (expected_collections or expected_doc_ids) else None,
            "keyword_coverage": round(keyword_coverage, 4) if keyword_coverage is not None else None,
            "faithfulness": grounded.get("faithfulness"),
            "answer_relevancy": grounded.get("answer_relevancy"),
            "groundedness_method": grounded.get("method"),
        }
        per_case.append(case_payload)

        precision_scores.append(precision)
        if recall is not None:
            recall_scores.append(recall)
        if expected_collections or expected_doc_ids:
            collection_hits.append(1 if relevant_hits > 0 else 0)
        if keyword_coverage is not None:
            keyword_coverages.append(keyword_coverage)
        if grounded.get("faithfulness") is not None:
            faithfulness_scores.append(float(grounded.get("faithfulness")))
        if grounded.get("answer_relevancy") is not None:
            answer_relevancy_scores.append(float(grounded.get("answer_relevancy")))

    metrics = {
        "avg_precision_at_k": round(sum(precision_scores) / max(len(precision_scores), 1), 4),
        "avg_recall_at_k": round(sum(recall_scores) / max(len(recall_scores), 1), 4) if recall_scores else None,
        "collection_hit_rate": round(sum(collection_hits) / max(len(collection_hits), 1), 4) if collection_hits else None,
        "avg_keyword_coverage": round(sum(keyword_coverages) / max(len(keyword_coverages), 1), 4) if keyword_coverages else None,
        "avg_faithfulness": round(sum(faithfulness_scores) / max(len(faithfulness_scores), 1), 4) if faithfulness_scores else None,
        "avg_answer_relevancy": round(sum(answer_relevancy_scores) / max(len(answer_relevancy_scores), 1), 4) if answer_relevancy_scores else None,
        "cases": len(request.cases),
    }

    summary = "RAG evaluation completed on synthetic cases."
    report = RAGEvaluationReport(summary=summary, metrics=metrics, per_case=per_case)
    await db.rag_evaluations.insert_one(report.model_dump())
    prior = await db.rag_evaluations.find({}, {"_id": 0}).sort("created_at", -1).limit(2).to_list(2)
    if len(prior) > 1:
        previous = prior[1]
        drop_faith = (previous.get("metrics", {}).get("avg_faithfulness") or 0) - (metrics.get("avg_faithfulness") or 0)
        drop_rel = (previous.get("metrics", {}).get("avg_answer_relevancy") or 0) - (metrics.get("avg_answer_relevancy") or 0)
        threshold_faith = float(get_integration_setting("rag_evaluation", "faithfulness_drop", "0.05") or 0.05)
        threshold_rel = float(get_integration_setting("rag_evaluation", "relevancy_drop", "0.05") or 0.05)
        if drop_faith >= threshold_faith or drop_rel >= threshold_rel:
            alert = {
                "event": "rag.eval.regression",
                "report_id": report.report_id,
                "prev_report_id": previous.get("report_id"),
                "drop_faithfulness": drop_faith,
                "drop_relevancy": drop_rel,
                "created_at": report.created_at,
            }
            await db.rag_evaluation_alerts.insert_one(alert)
    await record_audit(
        current_user.get("id", "unknown"),
        "rag.evaluation.completed",
        "rag_evaluation",
        report.report_id,
        metadata={"cases": len(request.cases), "metrics": metrics},
    )
    logger.info(
        "rag.evaluation.completed",
        extra={"payload": {"report_id": report.report_id, "cases": len(request.cases)}},
    )
    return report


@router.get("/rag/evaluate-gold")
async def evaluate_rag_gold(
    current_user: dict = Depends(require_permission("rag:read")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
) -> RAGEvaluationReport:
    """Evaluate RAG using the bundled gold dataset.

    Returns:
        RAGEvaluationReport: Evaluation report payload.
    """
    dataset_path = Path(__file__).resolve().parents[2] / "data" / "rag_gold_dataset.json"
    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail="Gold dataset not found")

    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    if payload.get("expand_from_taxonomy"):
        taxonomy_path = Path(__file__).resolve().parents[2] / payload.get("taxonomy_source", "banking_fraud_taxonomy_catalog_120.json")
        if taxonomy_path.exists():
            taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
            families = taxonomy.get("families", [])
            scenarios = taxonomy.get("scenarios", [])
            for family in families:
                family_name = family.get("family_name") or "fraud family"
                tags = family.get("tags", []) or []
                cases.append(
                    {
                        "query": f"Summarize {family_name} fraud patterns",
                        "expected_collections": ["taxonomy"],
                        "expected_keywords": [family_name] + tags,
                        "synthetic_only": True,
                        "reference_answer": f"{family_name} covers synthetic scenarios tagged with {', '.join(tags)}.",
                    }
                )
            for scenario in scenarios:
                scenario_name = scenario.get("scenario_name") or scenario.get("scenario_id")
                telemetry = scenario.get("telemetry_indicators", []) or []
                controls = scenario.get("recommended_controls", []) or []
                cases.append(
                    {
                        "query": f"What telemetry indicators are associated with {scenario_name}?",
                        "expected_collections": ["taxonomy"],
                        "expected_keywords": telemetry[:5],
                        "synthetic_only": True,
                        "reference_answer": f"Telemetry indicators include {', '.join(telemetry[:3])}.",
                    }
                )
                cases.append(
                    {
                        "query": f"What controls are recommended for {scenario_name}?",
                        "expected_collections": ["taxonomy"],
                        "expected_keywords": controls[:5],
                        "synthetic_only": True,
                        "reference_answer": f"Recommended controls include {', '.join(controls[:3])}.",
                    }
                )
    if not cases:
        raise HTTPException(status_code=400, detail="Gold dataset is empty")

    evaluation_request = RAGEvaluationRequest(cases=cases)
    report = await evaluate_rag(evaluation_request, current_user, db, llm_client)
    await record_audit(
        current_user.get("id", "unknown"),
        "rag.evaluation.gold.completed",
        "rag_evaluation",
        report.report_id,
        metadata={"dataset_id": payload.get("dataset_id")},
    )
    return report


@router.get("/rag/evaluations/history")
async def rag_evaluation_history(
    limit: int = 50,
    current_user: dict = Depends(require_permission("rag:read")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    """Return historical RAG evaluation reports."""
    records = await db.rag_evaluations.find({}, {"_id": 0}).sort("created_at", -1).to_list(max(limit, 1))
    await record_audit(
        current_user.get("id", "unknown"),
        "rag.evaluation.history",
        "rag_evaluation",
        "history",
        metadata={"limit": limit},
    )
    return {"items": records}


@router.get("/rag/evaluations/alerts")
async def rag_evaluation_alerts(
    limit: int = 20,
    current_user: dict = Depends(require_permission("rag:read")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    """Return regression alerts for RAG evaluations."""
    alerts = await db.rag_evaluation_alerts.find({}, {"_id": 0}).sort("created_at", -1).to_list(max(limit, 1))
    await record_audit(
        current_user.get("id", "unknown"),
        "rag.evaluation.alerts",
        "rag_evaluation",
        "alerts",
        metadata={"limit": limit},
    )
    return {"items": alerts}


@router.get("/rag/cache/telemetry")
async def rag_cache_telemetry(
    limit: int = 100,
    current_user: dict = Depends(require_permission("rag:read")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    """Return cache telemetry for CAG operations."""
    records = await db.rag_cache_telemetry.find({}, {"_id": 0}).sort("created_at", -1).to_list(max(limit, 1))
    hits = sum(1 for item in records if item.get("event") == "hit")
    misses = sum(1 for item in records if item.get("event") == "miss")
    total = hits + misses
    by_layer: Dict[str, int] = {}
    for item in records:
        layer = item.get("layer") or "unknown"
        by_layer[layer] = by_layer.get(layer, 0) + 1
    summary = {
        "hits": hits,
        "misses": misses,
        "hit_rate": round(hits / max(total, 1), 4),
        "by_layer": by_layer,
        "cache_stats": cag_cache.stats(),
        "last_event": records[0] if records else None,
    }
    await record_audit(
        current_user.get("id", "unknown"),
        "rag.cache.telemetry",
        "rag_cache",
        "telemetry",
        metadata={"limit": limit, "summary": summary},
    )
    return {"summary": summary, "items": records}
