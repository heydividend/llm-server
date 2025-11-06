from typing import List, Dict, Any, Iterable
import requests
from app.web_search.search_engines import web_search_google_cse_enhanced, web_search_bing_enhanced
from app.web_search.content_extraction import fetch_and_extract_content, create_robust_session, calculate_content_quality
from app.core.llm_providers import oai_stream

def web_fetch_enhanced(results: List[Dict[str, Any]], max_pages: int = 8, fast: bool = False) -> List[Dict[str, Any]]:
    session = create_robust_session()
    docs = []
    sorted_results = sorted(results[:max_pages], key=lambda x: -x.get("priority", 0))
    for result in sorted_results:
        url = result.get("url", "")
        if not url:
            continue
        content = fetch_and_extract_content(url, session, timeout=12 if fast else 25)
        if content:
            query = result.get("original_query", "")
            quality_score = calculate_content_quality(content["text"], query)
            content.update({
                "original_title": result.get("title", ""),
                "snippet": result.get("snippet", ""),
                "priority": result.get("priority", 0),
                "quality_score": quality_score,
                "source_type": result.get("source_type", "unknown")
            })
            docs.append(content)
        if len(docs) >= max_pages:
            break
    session.close()
    docs.sort(key=lambda x: (-x.get("quality_score", 0), -x.get("priority", 0)))
    return docs

def generate_enhanced_summary(question: str, sources: List[Dict[str, Any]]) -> Iterable[str]:
    if not sources:
        yield "I couldn't retrieve any reliable content from web sources."
        return
    source_contexts, source_map = [], []
    for i, source in enumerate(sources, 1):
        title = source.get("title", "Untitled")
        url = source.get("url", "")
        text = source.get("text", "")[:2000]
        priority = source.get("priority", 0)
        quality = source.get("quality_score", 0)
        quality_indicator = ""
        if priority >= 100:
            quality_indicator = " [OFFICIAL]"
        elif priority >= 80:
            quality_indicator = " [AUTHORITATIVE]"
        elif quality >= 70:
            quality_indicator = " [HIGH QUALITY]"
        source_map.append(f"[{i}] {title}{quality_indicator} — {url}")
        source_contexts.append(f"SOURCE [{i}]{quality_indicator}\nTITLE: {title}\nURL: {url}\nCONTENT:\n{text}\n")
    system_prompt = """You are an expert researcher and analyst. Provide accurate, well-sourced answers based on the provided sources.
Guidelines:
- Prioritize OFFICIAL and AUTHORITATIVE sources
- Use [n] citations for factual claims
- Be specific with numbers and dates
- If sources conflict, note it and cite both
- Clear structure; concise but thorough"""
    user_prompt = f"""QUESTION: {question}

{chr(10).join(source_contexts)}

Provide a comprehensive answer with inline [n] citations."""
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}]
    for chunk in oai_stream(messages, temperature=0.2, max_tokens=2000):
        yield chunk
    yield "\n\n## Sources\n"
    for src in source_map:
        yield f"- {src}\n"

def perform_enhanced_web_search(query: str, max_pages: int = 8, fast: bool = False) -> Iterable[str]:
    all_results = []
    google_results = web_search_google_cse_enhanced(query, num=10)
    for r in google_results:
        r["original_query"] = query
    all_results.extend(google_results)
    if len(google_results) < 8:
        bing_results = web_search_bing_enhanced(query, count=8)
        for r in bing_results:
            r["original_query"] = query
        existing_urls = {r["url"] for r in all_results}
        all_results.extend([r for r in bing_results if r["url"] not in existing_urls])
    if not all_results:
        yield "I couldn't retrieve any search results. Please check the search service configuration."
        return
    docs = web_fetch_enhanced(all_results, max_pages=max_pages, fast=fast)
    if not docs:
        yield "I found search results but couldn't access the full content. Here's what I found from the snippets:\n\n"
        for i, result in enumerate(all_results[:max_pages], 1):
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            url = result.get("url", "")
            indicator = " [OFFICIAL]" if result.get("priority", 0) >= 100 else ""
            yield f"[{i}] **{title}**{indicator}\n{snippet}\nSource: {url}\n\n"
        return
    for chunk in generate_enhanced_summary(query, docs):
        yield chunk