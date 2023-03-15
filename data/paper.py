class Paper:
    def __init__(self, dict):
        super().__init__()
        
        self.id = dict["id"]
        self.categories = dict["categories"].lower().split()
        
        # remove line breaks and excess whitespace in titles
        title = dict["title"].replace("\n", " ")
        self.title = " ".join(title.split())
    
        # remove line breaks and excess whitespace in abstracts
        abstract = dict["abstract"].replace("\n", " ")
        self.abstract = " ".join(abstract.split())
    
        # retrieve month and year from first published date
        self.month = dict["versions"][0]["created"].split()[2]
        self.year = int(dict["versions"][0]["created"].split()[3])
        
        # ensure first names are first, last names last, and no spaces
        authors_parsed = dict["authors_parsed"]
        authors = [author[::-1][1:] for author in authors_parsed]
        authors = [" ".join(author).strip() for author in authors]
        self.authors_string = ", ".join(authors)

    def has_category(self, categories):
        """
        Checks if the paper belongs to any of the categories in `categories`.
        
        Args:
            categories: List of category strings
            
        Returns:
            True if paper belongs to at least one category in `categories`,
            False otherwise.
        """
        for category in categories:
            if category in self.categories:
                return True
        return False
    
    @property
    def embedding_text(self):
        """
        Text used for embedding the paper, combining title, authors, year, and
        abstract.
        """
        text = ["Title: " + self.title,
                "By: " + self.authors_string,
                "From: " + str(self.year),
                "Abstract: " + self.abstract]
        return ". ".join(text)
    
    @property
    def metadata(self):
        return {"title": self.title,
                "authors": self.authors_string,
                "abstract": self.abstract,
                "year": self.year,
                "month": self.month}
    
    @property
    def has_valid_id(self):
        invalid_id = self.id.isupper() or self.id.islower()
        return not invalid_id