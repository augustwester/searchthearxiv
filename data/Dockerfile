FROM public.ecr.aws/lambda/python:3.10

COPY requirements.txt .
COPY paper.py .
COPY embed.py .
COPY setup_kaggle.py .
COPY run.sh .

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

CMD sh run.sh