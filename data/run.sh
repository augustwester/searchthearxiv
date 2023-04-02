# Create embeddings for new papers and add to Pinecone
python3 setup_kaggle.py
kaggle datasets download -d Cornell-University/arxiv
unzip arxiv.zip && rm arxiv.zip
python3 embed.py --no-confirmation

# Add new embeddings to embeddings dataset
kaggle datasets metadata awester/arxiv-embeddings
kaggle datasets download -d awester/arxiv-embeddings
unzip arxiv-embeddings.zip && rm arxiv-embeddings.zip
python3 update_kaggle.py
zip arxiv-embeddings.zip ml-arxiv-embeddings.json

# Upload new dataset version to Kaggle
mkdir kaggle-dataset
mv dataset-metadata.json kaggle-dataset
mv arxiv-embeddings.zip kaggle-dataset
cd kaggle-dataset
kaggle datasets version -m ""

echo "✅ Updated Kaggle dataset"