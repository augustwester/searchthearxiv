import logging
import os

import flask
import validators
from flask import render_template, request
from helpers import error, fetch_abstract, get_matches
from models import EMBEDDING_ADA_002
from openai import APIError, AuthenticationError, NotFoundError, OpenAI, RateLimitError
from pinecone import Pinecone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = flask.Flask(__name__)
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# connect to Pinecone
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index(os.environ["PINECONE_INDEX_NAME"])


@app.route("/")
def home() -> str:
    return render_template("index.html")


@app.route("/about")
def about() -> str:
    return render_template("about.html")


@app.route("/donate")
def donate() -> str:
    return render_template("donate.html")


@app.route("/search")
def search() -> str:
    query = request.args.get("query")
    k = 100  # number of matches to request from Pinecone

    # special logic for handling arxiv url queries
    if validators.url(query):
        arxiv_id = query.split("/")[-1]
        matches = index.fetch([arxiv_id]).vectors
        if len(matches) == 0:
            abstract = fetch_abstract(query)
            try:
                embed = (
                    client.embeddings.create(
                        input=abstract, model=EMBEDDING_ADA_002.name
                    )
                    .data[0]
                    .embedding
                )
            except (AuthenticationError, RateLimitError, NotFoundError, APIError) as e:
                logger.error("OpenAI error when embedding abstract: %s", e)
                return error("OpenAI not responding. Try again in a few minutes.")
            return get_matches(index, k, vector=embed, exclude=arxiv_id)
        return get_matches(index, k, id=arxiv_id, exclude=arxiv_id)

    # reject natural language queries longer than 200 characters
    if len(query) > 200:
        return error("Sorry! The length of your query cannot exceed 200 characters.")

    # embed query using OpenAI API
    try:
        embed = (
            client.embeddings.create(input=query, model=EMBEDDING_ADA_002.name)
            .data[0]
            .embedding
        )
    except AuthenticationError as e:
        logger.error("OpenAI authentication error: %s", e)
        return error("OpenAI authentication failed. Please check the API key.")
    except RateLimitError as e:
        logger.error("OpenAI rate limit error: %s", e)
        return error("Rate limit exceeded. Try again in a few minutes.")
    except NotFoundError as e:
        logger.error("OpenAI model not found: %s", e)
        return error("Embedding model not found. Please contact the administrator.")
    except APIError as e:
        logger.error("OpenAI API error: %s", e)
        return error("OpenAI not responding. Try again in a few minutes.")
    except Exception as e:
        logger.error("Unexpected error when fetching embedding from OpenAI: %s", e)
        return error("An unexpected error occurred. Try again in a few minutes.")

    # once we have the query embedding, find closest matches in Pinecone
    try:
        return get_matches(index, k, vector=embed)
    except Exception as e:
        logger.error("Encountered error when fetching matches from Pinecone: %s", e)
        return error("Pinecone not responding. Try again in a few minutes.")


@app.route("/robots.txt")
def robots() -> str:
    with open("static/robots.txt") as f:
        content = f.read()
    return content
