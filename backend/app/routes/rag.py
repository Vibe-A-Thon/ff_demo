import json
from fastapi import APIRouter, HTTPException
from app.db import db
from app.models import RAGDocument, RAGDocumentCreate, RAGHit, RAGQueryRequest, RAGResponse
from app.rag_utils import (
    build_context_snippets,
    contains_sensitive_identifiers,
    cosine_similarity,
    format_context_prompt,
    get_embedding,
    keyword_score,
    openai_client,
    simple_embed,
    tokenize,
)
from app.run_helpers import record_run_event

router = APIRouter()

@router.get("/rag/collections")
async def list_rag_collections():
    collections = await db.rag_documents.distinct("collection")
    return {"collections": sorted(collections)}

@router.get("/rag/documents")
async def list_rag_documents(collection: str | None = None, limit: int = 50):
    query = {}
    if collection:
        query["collection"] = collection
    docs = await db.rag_documents.find(query, {"_id": 0}).sort("created_at", -1).to_list(max(limit, 1))
    return docs

@router.post("/rag/documents")
async def create_rag_document(doc_data: RAGDocumentCreate):
    if doc_data.synthetic_only and contains_sensitive_identifiers(doc_data.content):
        raise HTTPException(status_code=400, detail="Synthetic-only mode: sensitive identifiers detected")
    embedding = await get_embedding(doc_data.content)
    doc = RAGDocument(**doc_data.model_dump(), embedding=embedding)
    await db.rag_documents.insert_one(doc.model_dump())
    return doc

@router.post("/rag/seed")
async def seed_rag_data(reset: bool = False):
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
                embedding = await get_embedding(content)
                doc = RAGDocument(
                    collection="taxonomy",
                    title=title,
                    content=content,
                    metadata=item,
                    embedding=embedding,
                )
                await db.rag_documents.insert_one(doc.model_dump())
                seeded += 1

    defaults = [
        {"collection": "attacks", "title": "Velocity Burst", "content": "Fraudsters split transactions into rapid bursts to evade single-threshold rules.", "metadata": {"team": "red"}},
        {"collection": "patterns", "title": "Account Takeover", "content": "ATO indicators: device mismatch, impossible travel, high-risk beneficiary changes.", "metadata": {"team": "blue"}},
        {"collection": "rules", "title": "VEL-001", "content": "Velocity rule: flag when tx_count > 5 in 10 minutes with shared device signals.", "metadata": {"team": "purple"}},
        {"collection": "explanations", "title": "Decision Template", "content": "Explain outcomes using top signals, rule hits, and confidence statement.", "metadata": {"team": "gold"}},
    ]
    for entry in defaults:
        embedding = await get_embedding(entry["content"])
        doc = RAGDocument(**entry, embedding=embedding)
        await db.rag_documents.insert_one(doc.model_dump())
        seeded += 1

    return {"message": "RAG data seeded", "count": seeded}

@router.post("/rag/retrieve")
async def rag_retrieve(request: RAGQueryRequest):
    if request.synthetic_only and contains_sensitive_identifiers(request.query):
        raise HTTPException(status_code=400, detail="Synthetic-only mode: sensitive identifiers detected")
    query = {}
    if request.collections:
        query["collection"] = {"$in": request.collections}
    if request.synthetic_only:
        query["synthetic_only"] = True
    docs = await db.rag_documents.find(query, {"_id": 0}).to_list(500)
    if not docs:
        return []

    query_embedding = await get_embedding(request.query)
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
    return hits

@router.post("/rag/query")
async def rag_query(request: RAGQueryRequest):
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
        query_embedding = await get_embedding(request.query)
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
    if openai_client and context_snippets:
        try:
            system_prompt = "You are a fraud defense assistant. Use only the provided context. If context is insufficient, say so. Keep responses synthetic-only and avoid real identifiers."
            prompt = format_context_prompt(context_snippets, request.query)
            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=400,
            )
            answer = response.choices[0].message.content
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

    return response
