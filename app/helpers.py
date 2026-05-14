import json
import time
import urllib.error
import urllib.request
from paper import Paper
from requests_html import HTMLSession
from collections import defaultdict

SEMANTIC_SCHOLAR_BATCH_URL = "https://api.semanticscholar.org/graph/v1/paper/batch?fields=citationCount"
SEMANTIC_SCHOLAR_MAX_RETRIES = 3
SEMANTIC_SCHOLAR_BASE_DELAY = 1  # seconds

def get_citation_counts(paper_ids):
    """Fetch citation counts from Semantic Scholar for a list of arXiv IDs.
    Uses exponential backoff on transient failures (up to 3 retries with 1s, 2s, 4s delays).
    Returns a dict mapping arXiv ID to citation count, or None if all attempts fail."""
    ids = [f"ARXIV:{pid}" for pid in paper_ids]
    data = json.dumps({"ids": ids}).encode("utf-8")
    last_error = None

    for attempt in range(1 + SEMANTIC_SCHOLAR_MAX_RETRIES):
        try:
            req = urllib.request.Request(
                SEMANTIC_SCHOLAR_BATCH_URL,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                results = json.loads(resp.read().decode("utf-8"))
            counts = {}
            for arxiv_id, result in zip(paper_ids, results):
                if result is not None and result.get("citationCount") is not None:
                    counts[arxiv_id] = result["citationCount"]
            return counts
        except urllib.error.HTTPError as e:
            last_error = e
            # Don't retry on client errors (4xx) other than 429 (rate limit)
            if 400 <= e.code < 500 and e.code != 429:
                print(f"Semantic Scholar returned non-retryable HTTP {e.code} (attempt {attempt + 1}): {e}", flush=True)
                break
            print(f"Semantic Scholar HTTP {e.code} (attempt {attempt + 1}/{1 + SEMANTIC_SCHOLAR_MAX_RETRIES}): {e}", flush=True)
        except Exception as e:
            last_error = e
            print(f"Semantic Scholar request failed (attempt {attempt + 1}/{1 + SEMANTIC_SCHOLAR_MAX_RETRIES}): {e}", flush=True)

        if attempt < SEMANTIC_SCHOLAR_MAX_RETRIES:
            delay = SEMANTIC_SCHOLAR_BASE_DELAY * (2 ** attempt)
            print(f"Retrying Semantic Scholar in {delay}s...", flush=True)
            time.sleep(delay)

    print(f"All Semantic Scholar attempts failed. Last error: {last_error}", flush=True)
    return None

def fetch_abstract(url):
    session = HTMLSession()
    r = session.get(url)
    content = r.html.find("#content-inner", first=True)
    abstract = content.find(".abstract", first=True).text
    return abstract

def avg_score(papers):
    avg_score = sum([p.score for p in papers]) / len(papers)
    return round(avg_score, 2)

def get_matches(index, k, vector=None, id=None, exclude=None):
    assert vector is not None or id is not None
    if vector is not None:
        top_k = index.query(vector=vector, top_k=k, include_metadata=True)
    else:
        top_k = index.query(id=id, top_k=k, include_metadata=True)
    matches = top_k["matches"]
    papers = [Paper(match) for match in matches if match["id"] != exclude]
    authors = get_authors(papers)
    
    top_papers = papers
    citation_counts = get_citation_counts([p.id for p in top_papers])
    citation_error = None
    if citation_counts is None:
        citation_error = "Citation counts are temporarily unavailable."
        citation_counts = {}
    for paper in top_papers:
        paper.citation_count = citation_counts.get(paper.id)
    
    papers = [paper.__dict__ for paper in top_papers]
    result = {"papers": papers, "authors": authors}
    if citation_error:
        result["citation_error"] = citation_error
    return json.dumps(result)

def get_authors(papers):
    authors = defaultdict(list)
    for paper in papers:
        for author in paper.authors_parsed:
            authors[author].append(paper)
    authors = [{"author": author,
                "papers": [paper.__dict__ for paper in papers],
                "avg_score": avg_score(papers)}
                for author, papers in authors.items()]
    authors = sorted(authors, key=lambda e: len(e["papers"]), reverse=True)
    return authors[:10]

def error(msg):
    return json.dumps({"error": msg})
