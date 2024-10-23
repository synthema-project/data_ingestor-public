FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11-slim
WORKDIR /app
RUN mkdir data
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r ./requirements.txt
COPY . .
EXPOSE 82
#ENV DATASET_PATH = /app/data/dataset
ENV DATASET_PATH = /app/datasets
#ENV DATABASE_PATH = /app/data/central_node.db #database
CMD ["python","main.py"]
