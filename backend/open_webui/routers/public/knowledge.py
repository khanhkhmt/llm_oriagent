"""
Public Knowledge/RAG API — POST /knowledge/query
"""
import logging, time
from fastapi import APIRouter, Depends, HTTPException, Request, status
from open_webui.routers.public.deps import PublicAPIContext, get_public_api_context
from open_webui.routers.public.rate_limit import check_rate_limit
from open_webui.routers.public.schemas import (
    PublicKnowledgeQueryRequest, PublicKnowledgeQueryResponse,
    PublicKnowledgeQueryResult, PublicKnowledgeQuerySource,
)

log = logging.getLogger(__name__)
router = APIRouter()

@router.post("/knowledge/query", response_model=PublicKnowledgeQueryResponse,
    summary="Query a knowledge base", description="Search a knowledge base using RAG retrieval.")
async def public_knowledge_query(request: Request, form_data: PublicKnowledgeQueryRequest,
    ctx: PublicAPIContext = Depends(get_public_api_context)):
    await check_rate_limit(request, ctx.user_id, "knowledge", ctx.request_id)
    # Validate top_k
    top_k = min(max(form_data.top_k, 1), 50)
    # Check knowledge exists and user has access
    from open_webui.models.knowledge import Knowledges
    knowledge = await Knowledges.get_knowledge_by_id(form_data.knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge base not found.")
    if knowledge.user_id != ctx.user_id and ctx.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied to this knowledge base.")
    # Query vector DB
    try:
        from open_webui.retrieval.vector.async_client import ASYNC_VECTOR_DB_CLIENT
        query_result = await ASYNC_VECTOR_DB_CLIENT.search(
            collection_name=form_data.knowledge_id,
            vectors=[],  # Will be filled by embedding
            limit=top_k,
        )
    except Exception:
        pass
    # Use retrieval utility for proper embedding + search
    try:
        from open_webui.routers.retrieval import get_embedding_function
        ef = get_embedding_function(
            request.app.state.config.RAG_EMBEDDING_ENGINE,
            request.app.state.config.RAG_EMBEDDING_MODEL,
            request.app.state.config.RAG_OPENAI_API_BASE_URL,
            request.app.state.config.RAG_OPENAI_API_KEY,
            request.app.state.config.RAG_EMBEDDING_BATCH_SIZE,
        )
        from open_webui.retrieval.utils import query_collection
        result = await query_collection(
            collection_names=[form_data.knowledge_id],
            query=form_data.query,
            embedding_function=ef,
            k=top_k,
        )
        results = []
        if result and isinstance(result, dict):
            documents = result.get("documents", [[]])
            distances = result.get("distances", [[]])
            metadatas = result.get("metadatas", [[]])
            for i, doc_list in enumerate(documents):
                for j, doc in enumerate(doc_list):
                    score = 1.0 - (distances[i][j] if i < len(distances) and j < len(distances[i]) else 0.0)
                    meta = metadatas[i][j] if i < len(metadatas) and j < len(metadatas[i]) else {}
                    source = None
                    if meta:
                        source = PublicKnowledgeQuerySource(
                            file_id=meta.get("file_id"),
                            filename=meta.get("name") or meta.get("filename"),
                            page=meta.get("page"),
                        )
                    results.append(PublicKnowledgeQueryResult(content=doc, score=round(score, 4), source=source))
        log.info("Public knowledge query: req=%s results=%d", ctx.request_id, len(results))
        return PublicKnowledgeQueryResponse(object="knowledge.query", data=results[:top_k])
    except HTTPException:
        raise
    except Exception as e:
        log.error("Public knowledge query error: req=%s error=%s", ctx.request_id, str(e))
        raise HTTPException(status_code=500, detail="Knowledge query failed.")
