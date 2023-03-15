![searchthearXiv](.github/logo.png)

This repo contains the implementation of [searchthearxiv.com](https://searchthearxiv.com), a simple semantic search engine for more than 250,000 ML papers on arXiv (and counting). The code is separated into two parts, `app` and `data`. `app` contains the implementation of both the frontend and backend of the web app, while `data` is responsible for updating the database at regular intervals using OpenAI and [Pinecone](https://www.pinecone.io). Both `app` and `data` contain a Dockerfile for easy deployment to cloud platforms. I don't expect (or encourage) anyone to run a clone of the project on their own (that would be weird), but it might serve as inspiration for people building a similar type of semantic search engine.

In order to run the code, you need to supply the following list of environment variables:

```
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_API_KEY=your_kaggle_api_key
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_pinecone_index_name
```

The Kaggle username and API key are required to fetch the [arXiv dataset](https://www.kaggle.com/datasets/Cornell-University/arxiv) maintained (and updated weekly) by Cornell University. The OpenAI API key is used to embed new papers using the `text-embedding-ada-002` model. The Pinecone API key and index name are used to connect to the index (i.e. vector database) hosted on Pinecone.

To embed papers on your own, you can run `embed.py` in `data` after setting the environment variables and creating a Pinecone index. If you don't want to use Pinecone, you are free to modify the code however you want. Since the index will initially be empty, the script will embed all ML papers (again, more than 250,000). However, before doing so, it will estimate a price using OpenAI's [tiktoken](https://github.com/openai/tiktoken) tokenizer and ask you to confirm. You can skip this step by running `python3 embed.py --no-confirmation`. Before you do so, however, please note that I expect to publish the full set of embeddings (more than 10GB) soon. Feel free to follow me on [Twitter](https://twitter.com/augustwester) for updates on this.

If you like searchthearxiv.com and would like to see something improved, feel free to submit a pull request 🤗
