class Paper(dict):
    def __init__(self, match):
        super().__init__()
        
        self.id = match["id"]
        self.score = round(match["score"], 2)
        
        metadata = match["metadata"]
        self.title = metadata["title"]
        self.authors = metadata["authors"]
        self.abstract = metadata["abstract"]
        self.year = metadata["year"]
        self.month = metadata["month"]
        
        authors_parsed = self.authors.split(",")
        self.authors_parsed = [author.strip() for author in authors_parsed]