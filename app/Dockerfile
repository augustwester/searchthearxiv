FROM python:3.10.6-slim
EXPOSE 8000

COPY app.py .
COPY helpers.py .
COPY paper.py .
COPY static static/
COPY templates templates/
COPY requirements.txt .

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

CMD gunicorn --bind 0.0.0.0:8000 app:app
