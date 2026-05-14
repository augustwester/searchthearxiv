import json
import logging
import time
import urllib.error
import urllib.request
from collections import defaultdict
from typing import Any

from paper import Paper
from requests_html import HTMLSession

logger = logging.getLogger(__name__)

SEMANTIC_SCHOLAR_BATCH_URL = (
    "https://api.semanticscholar.org/graph/v1/paper/batch?fields=citationCount"
)
SEMANTIC_SCHOLAR_MAX_RETRIES = 3
SEMANTIC_SCHOLAR_BASE_DELAY = 1  # seconds


def get_citation_counts(paper_ids: list[str]) -> dict[str, int] | None:
    """Fetch citation counts from Semantic Scholar for arXiv IDs.

    Uses exponential backoff on transient failures
    (up to 3 retries with 1s, 2s, 4s delays).
    Returns a dict mapping arXiv ID to citation count,
    or None if all attempts fail.
    """
    ids = [f"ARXIV:{pid}" for pid in paper_ids]
    data = json.dumps({"ids": ids}).encode("utf-8")
    last_error: Exception | None = None

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
            counts: dict[str, int] = {}
            for arxiv_id, result in zip(paper_ids, results, strict=True):
                if result is not None and result.get("citationCount") is not None:
                    counts[arxiv_id] = result["citationCount"]
            return counts
        except urllib.error.HTTPError as e:
            last_error = e
            # Don't retry on client errors (4xx) other than 429 (rate limit)
            if 400 <= e.code < 500 and e.code != 429:
                logger.error(
                    "Semantic Scholar returned non-retryable HTTP %d (attempt %d): %s",
                    e.code,
                    attempt + 1,
                    e,
                )
                break
            logger.warning(
                "Semantic Scholar HTTP %d (attempt %d/%d): %s",
                e.code,
                attempt + 1,
                1 + SEMANTIC_SCHOLAR_MAX_RETRIES,
                e,
            )
        except Exception as e:
            last_error = e
            logger.warning(
                "Semantic Scholar request failed (attempt %d/%d): %s",
                attempt + 1,
                1 + SEMANTIC_SCHOLAR_MAX_RETRIES,
                e,
            )

        if attempt < SEMANTIC_SCHOLAR_MAX_RETRIES:
            delay = SEMANTIC_SCHOLAR_BASE_DELAY * (2**attempt)
            logger.warning("Retrying Semantic Scholar in %ds...", delay)
            time.sleep(delay)

    logger.error(
        "All Semantic Scholar attempts failed. Last error: %s",
        last_error,
    )
    return None


def fetch_abstract(url: str) -> str:
    session = HTMLSession()
    r = session.get(url)
    content = r.html.find("#content-inner", first=True)
    abstract = content.find(".abstract", first=True).text
    return abstract


def avg_score(papers: list[Paper]) -> float:
    score = sum([p.score for p in papers]) / len(papers)
    return round(score, 2)


def get_matches(
    index: Any,  # noqa: ANN401
    k: int,
    vector: list[float] | None = None,
    id: str | None = None,
    exclude: str | None = None,
) -> str:
    assert vector is not None or id is not None
    if vector is not None:
        top_k = index.query(vector=vector, top_k=k, include_metadata=True)
    else:
        top_k = index.query(id=id, top_k=k, include_metadata=True)
    matches = top_k["matches"]
    papers = [Paper(match) for match in matches if match["id"] != exclude]
    authors = get_authors(papers)

    top_papers = papers
    citation_counts = get_citation_counts([p.id for p in top_papers]) or {}
    citation_error = None
    if citation_counts is None:
        citation_error = "Citation counts are temporarily unavailable."
        citation_counts = {}
    for paper in top_papers:
        paper.citation_count = citation_counts.get(paper.id)

    paper_dicts = [paper.__dict__ for paper in top_papers]
    result: dict[str, Any] = {"papers": paper_dicts, "authors": authors}
    if citation_error:
        result["citation_error"] = citation_error
    return json.dumps(result)


def get_authors(papers: list[Paper]) -> list[dict[str, Any]]:
    author_map = defaultdict(list)
    for paper in papers:
        for author in paper.authors_parsed:
            author_map[author].append(paper)
    authors = [
        {
            "author": author,
            "papers": [paper.__dict__ for paper in author_papers],
            "avg_score": avg_score(author_papers),
        }
        for author, author_papers in author_map.items()
    ]
    authors = sorted(authors, key=lambda e: len(e["papers"]), reverse=True)
    return authors[:10]


def error(msg: str) -> str:
    return json.dumps({"error": msg})
