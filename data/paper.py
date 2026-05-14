from typing import Any


class Paper:
    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__()

        self.id: str = data["id"]
        self.categories: list[str] = data["categories"].lower().split()

        # remove line breaks and excess whitespace in titles
        title = data["title"].replace("\n", " ")
        self.title = " ".join(title.split())

        # remove line breaks and excess whitespace in abstracts
        abstract = data["abstract"].replace("\n", " ")
        self.abstract = " ".join(abstract.split())

        # retrieve month and year from first published date
        self.month: str = data["versions"][0]["created"].split()[2]
        self.year: int = int(data["versions"][0]["created"].split()[3])

        # ensure first names are first, last names last, and no spaces
        authors_parsed: list[list[str]] = data["authors_parsed"]
        authors = [author[::-1][1:] for author in authors_parsed]
        author_names = [" ".join(author).strip() for author in authors]
        self.authors_string = ", ".join(author_names)

    def has_category(self, categories: list[str]) -> bool:
        """
        Checks if the paper belongs to any of the categories in `categories`.

        Args:
            categories: List of category strings

        Returns:
            True if paper belongs to at least one category in `categories`,
            False otherwise.
        """
        return any(category in self.categories for category in categories)

    @property
    def embedding_text(self) -> str:
        """
        Text used for embedding the paper, combining title, authors, year, and
        abstract.
        """
        text = [
            "Title: " + self.title,
            "By: " + self.authors_string,
            "From: " + str(self.year),
            "Abstract: " + self.abstract,
        ]
        return ". ".join(text)

    @property
    def metadata(self) -> dict[str, str | int]:
        return {
            "title": self.title,
            "authors": self.authors_string,
            "abstract": self.abstract,
            "year": self.year,
            "month": self.month,
        }

    @property
    def has_valid_id(self) -> bool:
        invalid_id = self.id.isupper() or self.id.islower()
        return not invalid_id
