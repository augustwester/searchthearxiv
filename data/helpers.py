import json
from openai import OpenAI
import os
import tiktoken
from pinecone import Pinecone
from tqdm import tqdm
from paper import Paper

def load_data(file_path, categories, start_year):
    """
    Returns a generator over the papers contained in `file_path`, belonging to
    the categories in `categories`, and published in or after `start_year`.
    
    Args:
        file_path: The path to the JSON file containing the arXiv data
        categories: A list of category strings
        start_year: An integer specifying the earliest year to include
        
    Returns:
        A generator over the papers satisfying the criteria.
    """
    json_file = open(file_path, "r", encoding="utf-8")
    papers = (Paper(json.loads(line)) for line in json_file)
    papers = (paper for paper in papers
              if paper.has_category(categories) and paper.has_valid_id)
    return (paper for paper in papers if paper.year >= start_year)

def pinecone_embedding_count(index_name):
    """
    Helper function to get the total number of embeddings stored in the Pinecone
    index with the name specified in `index_name`.
    
    Args:
        index_name: The name of the Pinecone index
        
    Returns:
        The total number of embeddings stored in the Pinecone index.
    """
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index = pc.Index(index_name)
    return index.describe_index_stats()["total_vector_count"]

def estimate_embedding_price(papers, price_per_1k):
    """
    Estimates the price of embedding the papers in `papers` using OpenAI's
    tiktoken tokenizer.
    
    Args:
        papers: A list of `Paper` objects
        price_per_1k: Price per 1000 tokens
    
    Returns:
        A tuple containing the estimated number of tokens and a price.
    """
    enc = tiktoken.get_encoding("gpt2")
    num_tokens = 0
    for paper in tqdm(papers):
        num_tokens += len(enc.encode(paper.embedding_text))
    price = num_tokens / 1000 * price_per_1k
    return num_tokens, price

def get_embeddings(texts, model="text-embedding-ada-002"):
    """
    Returns a list of embeddings for each string in `texts` using the OpenAI
    embedding model specified in `model`.
    
    Args:
        texts: A list of strings to embed
        model: The name of the OpenAI embedding model to use
        
    Returns:
        A list of embeddings.
    """
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return client.embeddings.create(input=texts, model=model).data

def embed_and_upsert(papers, index_name, model, batch_size=50):
    """
    Embeds the embedding text of each paper in `papers` using the embedding
    model specified in `model`. The embeddings are then upserted to the Pinecone
    index with name `index_name` in batches of size `batch_size`.
    
    Args:
        papers: The list of papers for which to embed their embedding text
        index_name: The name of the index in which the embeddings will be upserted
        model: The name of the OpenAI embedding model to use
        batch_size: The batch size to use when upserting embeddings to Pinecone
    """
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    with pc.Index(index_name, pool_threads=5) as index:
        for i in tqdm(range(0, len(papers), batch_size)):
            batch = papers[i:i+batch_size]
            texts = [paper.embedding_text for paper in batch]
            embed_data = get_embeddings(texts, model)
        
            pc_data = [(p.id, e.embedding, p.metadata)
                       for p, e in zip(batch, embed_data, strict=True)]
            index.upsert(pc_data)
