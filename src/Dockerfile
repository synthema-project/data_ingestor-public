FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11-slim
WORKDIR /app
RUN mkdir data
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r ./requirements.txt
COPY . .
EXPOSE 82
#ENV DATASET_PATH = /app/data/dataset
#ENV DATASET_PATH = /app/datasets
#ENV PYTHONPATH = /app/src
#VOLUME /app/datasets
#ENV DATABASE_PATH = /app/data/central_node.db #database
ENV MINIO_ENDPOINT = obstorageapi.k8s.synthema.rid-intrasoft.eu
ENV MINIO_BUCKET_NAME = data-annotation
ENV MINIO_ACCESS_KEY = mqcqwECvoga6pkDRhOUz
ENV MINIO_SECRET_KEY = EN6t1TWZELRhn1LyGoi6ubtApmXoUJfsny9tRYz9

CMD ["python","main.py"]
