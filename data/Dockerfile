FROM python:3.10.6-slim

RUN apt-get update
RUN apt-get -y install zip unzip

COPY requirements.txt .
COPY paper.py .
COPY embed.py .
COPY helpers.py .
COPY setup_kaggle.py .
COPY update_kaggle.py .
COPY run.sh .

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

CMD sh run.sh
