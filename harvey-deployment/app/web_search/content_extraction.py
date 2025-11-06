import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any, Optional
from readability import Document
import trafilatura
from bs4 import BeautifulSoup
import newspaper
from urllib.parse import urlparse

def create_robust_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    return session

def extract_text_multiple_methods(html_content: str, url: str) -> Dict[str, str]:
    results = {}
    try:
        text = trafilatura.extract(html_content, include_links=False, include_images=False)
        if text and len(text) > 200:
            results['trafilatura'] = text
    except Exception:
        pass
    try:
        doc = Document(html_content)
        title = doc.short_title()
        content = doc.summary()
        text = BeautifulSoup(content, 'html.parser').get_text()
        if text and len(text) > 200:
            results['readability'] = {'title': title, 'text': text}
    except Exception:
        pass
    try:
        article = newspaper.Article(url)
        article.set_html(html_content)
        article.parse()
        if article.text and len(article.text) > 200:
            results['newspaper'] = {
                'title': article.title,
                'text': article.text,
                'authors': article.authors,
                'publish_date': article.publish_date
            }
    except Exception:
        pass
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        if text and len(text) > 200:
            results['beautifulsoup'] = text
    except Exception:
        pass
    return results

def calculate_content_quality(text: str, query: str) -> float:
    if not text or len(text) < 100:
        return 0.0
    score = 0.0
    query_lower = query.lower()
    text_lower = text.lower()
    length_score = min(len(text) / 5000, 1.0)
    score += length_score * 20
    query_words = query_lower.split()
    matches = sum(1 for word in query_words if word in text_lower)
    if query_words:
        relevance_score = matches / len(query_words)
        score += relevance_score * 50
    structure_indicators = ['\n\n', '. ', ', ', ':', ';']
    structure_score = sum(min(text.count(ind) / 10, 1) for ind in structure_indicators)
    score += structure_score * 5
    sentences = text.split('.')
    if len(sentences) > 1:
        unique_sentences = len(set(sentences))
        repetition_penalty = (len(sentences) - unique_sentences) / len(sentences)
        score -= repetition_penalty * 20
    return max(0.0, min(100.0, score))

def fetch_and_extract_content(url: str, session: requests.Session, timeout: int = 25) -> Optional[Dict[str, Any]]:
    try:
        response = session.get(url, timeout=timeout, allow_redirects=True)
        if response.status_code != 200:
            return None
        content_type = response.headers.get('content-type', '').lower()
        if 'html' not in content_type and 'text' not in content_type:
            return None
        html_content = response.text
        extraction_results = extract_text_multiple_methods(html_content, url)
        if not extraction_results:
            return None
        best_text, best_title = "", ""
        for method, result in extraction_results.items():
            if isinstance(result, str):
                text, title = result, ""
            else:
                text, title = result.get('text', ''), result.get('title', '')
            if text and len(text) > 200 and len(text) > len(best_text):
                best_text, best_title = text, title
        if not best_text:
            return None
        best_text = ' '.join(best_text.split())[:12000]
        return {"url": url, "title": best_title or "Untitled", "text": best_text,
                "length": len(best_text), "extraction_methods": list(extraction_results.keys())}
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None