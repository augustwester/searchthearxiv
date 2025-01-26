import json
from paper import Paper
from requests_html import HTMLSession
from collections import defaultdict

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
    
    papers = [paper.__dict__ for paper in papers[:10]]
    return json.dumps({"papers": papers, "authors": authors})

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
