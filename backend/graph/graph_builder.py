from __future__ import annotations

import logging
from typing import Dict, Any, List, Tuple

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END

from ..config import get_settings
from ..memory import get_history
from ..vectorstore import similarity_search, similarity_search_with_score
from .state import GraphState, RouteType


logger = logging.getLogger(__name__)
settings = get_settings()


def _get_llm():
    return ChatOpenAI(
        model=settings.model_name,
        temperature=0.2,
    )


def classify_query(state: GraphState) -> GraphState:
    """
    Router that uses embeddings + retrieval signals to decide between:
    - documents: question is best answered from uploaded docs
    - general: general world knowledge / reasoning is enough
    - web: needs real‑time or external web information
    """
    query = state["query"]
    session_id = state["session_id"]
    history = state.get("history") or []

    # 1) Look up how strongly this query matches the user's documents (embedding-based)
    doc_scores: List[Tuple[Any, float]] = []
    try:
        doc_scores = similarity_search_with_score(
            query,
            k=4,
            metadata_filter={"session_id": session_id},
        )
    except Exception as exc:
        logger.warning("Router could not query vector store for routing: %s", exc)

    has_docs = len(doc_scores) > 0
    raw_max_score = max((s for _, s in doc_scores), default=0.0)
    # Ensure we always work with a plain Python float for JSON / Pydantic
    max_score: float = float(raw_max_score)

    # Prepare a compact view of top candidates for the LLM
    top_docs_preview = []
    for doc, score in doc_scores[:3]:
        top_docs_preview.append(
            {
                "score": float(score),
                "source": (doc.metadata or {}).get("source", "unknown"),
                "snippet": doc.page_content[:500],
            }
        )

    # 2) Build a compact conversation history string for context-aware routing
    history_text = ""
    if history:
        msgs = [f"{m['role']}: {m['content']}" for m in history[-6:]]
        history_text = "\n".join(msgs)

    # 3) Ask a small router LLM, giving it the query + similarity scores + snippets + history
    llm = _get_llm()
    system_prompt = (
        "You are a strict router.\n"
        "You MUST output exactly one word: 'documents', 'general', or 'web'.\n\n"
        "Inputs you receive:\n"
        "- The recent conversation (previous few turns).\n"
        "- The user question.\n"
        "- Whether any documents exist for this session.\n"
        "- The top retrieved document snippets from a vector store and their similarity scores "
        "(higher score means more semantically similar).\n\n"
        "Routing rules (take the conversation into account):\n"
        "- Choose 'documents' when the question is mainly about information that seems to be contained in the retrieved "
        "snippets (high similarity scores and relevant content).\n"
        "- Choose 'web' when the question clearly needs very recent, real‑time, or external data that a static document "
        "probably will not contain (e.g., up‑to‑date exchange rates, stock prices, weather today, latest news headlines, "
        "live sports scores, etc.).\n"
        "- If the user asks for the *current* value, price, rate, weather, news, or any other quantity that obviously changes "
        "over time (for example: 'what is the current USD to INR rate', 'now tell me the value of 1 dollar in rupees'), "
        "you MUST choose 'web', even if documents exist and even if some snippets look similar.\n"
        "- Otherwise choose 'general'.\n\n"
        "Prefer 'documents' over 'general' when you are unsure but there are strong, relevant document matches.\n"
        "Also, if the user previously asked for an exchange rate or other web-only data and now sends a short follow-up "
        "like a number or 'that amount', you should still choose 'web', since this is a follow-up that needs web data."
    )

    user_prompt = (
        "Conversation so far:\n"
        "{history}\n\n"
        "Current user question:\n"
        "{query}\n\n"
        f"Any documents in this session: {has_docs}\n"
        f"Top similarity score: {max_score}\n"
        "Top retrieved snippets (JSON list):\n"
        "{docs_preview}\n\n"
        "Respond with ONLY one word: documents, general, or web."
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", user_prompt),
        ]
    )

    chain = prompt | llm | StrOutputParser()
    route_raw = chain.invoke(
        {
            "history": history_text or "(no prior messages)",
            "query": query,
            "docs_preview": top_docs_preview,
        }
    ).strip().lower()

    if route_raw not in {"documents", "web", "general"}:
        route_raw = "general"

    route: RouteType = route_raw  # type: ignore

    logger.info(
        "Query routed as '%s' | query='%s' | has_docs=%s | max_score=%.3f",
        route,
        query,
        has_docs,
        max_score,
    )

    debug = dict(state.get("debug", {}))
    debug["route"] = route
    debug["router_reason"] = "embedding+llm"
    debug["routing_max_similarity"] = float(max_score)
    debug["routing_docs_preview"] = top_docs_preview

    return {**state, "route": route, "debug": debug}


def rewrite_query(state: GraphState) -> GraphState:
    llm = _get_llm()
    system = (
        "You lightly rewrite user questions to better match retrieval from a vector database.\n"
        "CRITICAL RULES:\n"
        "- Do NOT change the domain or topic of the question.\n"
        "- Do NOT introduce new entities that are not clearly implied by the question.\n"
        "- Especially avoid mapping generic words (like 'traveller', 'customer', 'player') to specific games, movies, or pop culture.\n"
        "- Keep all key nouns, names, dates, amounts, and entities from the original question.\n"
        "- Only clarify or expand when it helps retrieval (e.g., spell out abbreviations, make implicit constraints explicit).\n"
        "- If the question already looks retrieval‑ready, return it unchanged."
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("user", "{query}"),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    rewritten = chain.invoke({"query": state["query"]}).strip()
    debug = dict(state.get("debug", {}))
    debug["rewritten_query"] = rewritten
    logger.info("Rewrote query '%s' -> '%s'", state["query"], rewritten)
    return {**state, "rewritten_query": rewritten, "debug": debug}


def retrieve_documents(state: GraphState) -> GraphState:
    query = state.get("rewritten_query") or state["query"]
    session_id = state["session_id"]
    docs = similarity_search(query, k=5, metadata_filter={"session_id": session_id})
    logger.info("Retrieved %d candidate documents for query='%s'", len(docs), query)
    return {**state, "documents": docs}


def grade_documents(state: GraphState) -> GraphState:
    docs = state.get("documents") or []
    if not docs:
        return state

    llm = _get_llm()
    system = (
        "You are a relevance grader for retrieved context documents.\n"
        "Given a question and a document snippet, respond with 'yes' if the snippet is helpful,\n"
        "otherwise respond with 'no'. Only answer 'yes' or 'no'."
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("user", "Question: {question}\n\nDocument:\n{document}"),
        ]
    )
    chain = prompt | llm | StrOutputParser()

    filtered_docs = []
    kept_indices: List[int] = []
    for idx, doc in enumerate(docs):
        answer = chain.invoke(
            {"question": state["query"], "document": doc.page_content[:1500]}
        ).strip().lower()
        is_relevant = "yes" in answer
        if is_relevant:
            filtered_docs.append(doc)
            kept_indices.append(idx)

    # Safety net: never drop everything. If the grader rejected all,
    # keep the top-1 document so the answer node still gets some context.
    if not filtered_docs and docs:
        filtered_docs = [docs[0]]
        kept_indices = [0]

    logger.info(
        "Graded %d documents; kept %d as relevant.",
        len(docs),
        len(filtered_docs),
    )
    debug = dict(state.get("debug", {}))
    debug["kept_doc_indices"] = kept_indices
    return {**state, "documents": filtered_docs, "debug": debug}


def answer_with_rag(state: GraphState) -> GraphState:
    llm = _get_llm()
    history = state.get("history") or []
    docs = state.get("documents") or []

    context_blocks = []
    for d in docs:
        meta = d.metadata or {}
        src = meta.get("source", "unknown")
        context_blocks.append(f"[{src}]\n{d.page_content}")
    context_text = "\n\n---\n\n".join(context_blocks) if context_blocks else "No relevant documents were found."

    system = (
        "You are an AI assistant answering questions using the provided context from documents when available.\n"
        "Use the context faithfully and say explicitly when the context does not contain the answer."
    )

    history_text = ""
    if history:
        msgs = [f"{m['role']}: {m['content']}" for m in history[-6:]]
        history_text = "\n".join(msgs)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "user",
                "Conversation so far:\n{history}\n\n"
                "Context from documents:\n{context}\n\n"
                "User question:\n{query}",
            ),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke(
        {
            "history": history_text or "(no prior messages)",
            "context": context_text,
            "query": state["query"],
        }
    ).strip()
    return {**state, "answer": answer}


def answer_with_general_llm(state: GraphState) -> GraphState:
    llm = _get_llm()
    history = state.get("history") or []

    history_text = ""
    if history:
        msgs = [f"{m['role']}: {m['content']}" for m in history[-6:]]
        history_text = "\n".join(msgs)

    system = (
        "You are a helpful AI assistant.\n"
        "Use general world knowledge and reasoning to answer the user's question.\n"
        "If you are unsure, say you are unsure."
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("user", "Conversation so far:\n{history}\n\nUser question:\n{query}"),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke(
        {
            "history": history_text or "(no prior messages)",
            "query": state["query"],
        }
    ).strip()
    return {**state, "answer": answer}


def answer_with_web(state: GraphState) -> GraphState:
    llm = _get_llm()
    tool = TavilySearchResults(api_key=settings.tavily_api_key, max_results=5)

    history = state.get("history") or []
    history_text = ""
    if history:
        msgs = [f"{m['role']}: {m['content']}" for m in history[-6:]]
        history_text = "\n".join(msgs)

    # 1) Call Tavily directly to get structured web results
    try:
        search_results = tool.invoke({"query": state["query"]})
    except Exception as exc:
        logger.warning("Web search failed: %s", exc)
        search_results = []

    # 2) Summarise those results with the LLM, taking conversation into account
    system = (
        "You are a web-enabled assistant.\n"
        "You are given structured web search results, the recent conversation, and the current user question.\n"
        "Use ONLY the provided results for any real-time / numerical data, but you MAY use the conversation context "
        "to understand what quantities (like 'that amount', or a number such as 901.49) refer to.\n"
        "For example, if earlier messages mention a total cost in USD and the user now asks to convert 'that amount' "
        "using the current exchange rate, you should combine the exchange rate from the web results with the amount "
        "mentioned in the conversation.\n"
        "If the results are empty or do not contain the needed data, say that you cannot find a reliable up-to-date value."
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "user",
                "Conversation so far:\n{history}\n\n"
                "Current user question:\n{query}\n\n"
                "Web search results (JSON list):\n{results}",
            ),
        ]
    )

    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke(
        {
            "history": history_text or "(no prior messages)",
            "query": state["query"],
            "results": search_results,
        }
    ).strip()

    debug = dict(state.get("debug", {}))
    debug["web_search_used"] = True
    debug["web_raw_results_count"] = len(search_results) if isinstance(search_results, list) else None
    return {**state, "answer": answer, "debug": debug}


def build_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("classify", classify_query)
    workflow.add_node("rewrite", rewrite_query)
    workflow.add_node("retrieve", retrieve_documents)
    workflow.add_node("grade", grade_documents)
    workflow.add_node("answer_rag", answer_with_rag)
    workflow.add_node("answer_general", answer_with_general_llm)
    workflow.add_node("answer_web", answer_with_web)

    workflow.set_entry_point("classify")

    # Routing after classification
    def route_after_classification(state: GraphState) -> str:
        route = state.get("route", "general")
        if route == "documents":
            return "rewrite"
        if route == "web":
            return "answer_web"
        return "answer_general"

    workflow.add_conditional_edges(
        "classify",
        route_after_classification,
        {
            "rewrite": "rewrite",
            "answer_web": "answer_web",
            "answer_general": "answer_general",
        },
    )

    # RAG path
    workflow.add_edge("rewrite", "retrieve")
    workflow.add_edge("retrieve", "grade")
    workflow.add_edge("grade", "answer_rag")

    # Terminal nodes
    workflow.add_edge("answer_rag", END)
    workflow.add_edge("answer_general", END)
    workflow.add_edge("answer_web", END)

    graph = workflow.compile()
    return graph

