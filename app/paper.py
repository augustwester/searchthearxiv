from typing import Any


class Paper(dict):
    def __init__(self, match: dict[str, Any]) -> None:
        super().__init__()

        self.id: str = match["id"]
        self.score = round(match["score"], 2)

        metadata = match["metadata"]
        self.title: str = metadata["title"]
        self.authors: str = metadata["authors"]
        self.abstract: str = metadata["abstract"]
        self.year: int = metadata["year"]
        self.month: str = metadata["month"]

        authors_parsed = self.authors.split(",")
        self.authors_parsed = [author.strip() for author in authors_parsed]

        self.citation_count: int | None = None
