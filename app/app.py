import flask
from openai import OpenAI
import os
from pinecone import Pinecone
import validators
from flask import render_template, request
from helpers import get_matches, fetch_abstract, error

app = flask.Flask(__name__)
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

MODEL = "text-embedding-ada-002"

# connect to Pinecone
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index("search-the-arxiv")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/search")
def search():
    query = request.args.get("query")
    K = 100 # number of matches to request from Pinecone
    
    # special logic for handling arxiv url queries
    if validators.url(query):
        arxiv_id = query.split("/")[-1]
        matches = index.fetch([arxiv_id])["vectors"]
        if len(matches) == 0:
            abstract = fetch_abstract(query)
            embed = client.embeddings.create(input=abstract, model=MODEL).data[0].embedding
            return get_matches(index, K, vector=embed, exclude=arxiv_id)
        return get_matches(index, K, id=arxiv_id, exclude=arxiv_id)
    
    # reject natural language queries longer than 200 characters
    if len(query) > 200:
        return error("Sorry! The length of your query cannot exceed 200 characters.")
    
    # embed query using OpenAI API
    try:
        embed = client.embeddings.create(input=query, model=MODEL).data[0].embedding
    except Exception as e:
        print(f"Encountered error when fetching embedding from OpenAI: {e}", flush=True)
        return error("OpenAI not responding. Try again in a few minutes.")
    
    # once we have the query embedding, find closest matches in Pinecone
    try:
        return get_matches(index, K, vector=embed)
    except Exception as e:
        print(f"Encountered error when fetching matches from Pinecone: {e}", flush=True)
        return error("Pinecone not responding. Try again in a few minutes.")

@app.route("/robots.txt")
def robots():
    with open("static/robots.txt", "r") as f:
        content = f.read()
    return content
