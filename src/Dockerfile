FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11-slim
WORKDIR /app
RUN mkdir data
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r ./requirements.txt
COPY . .
EXPOSE 82
#ENV DATASET_PATH = /app/data/dataset
ENV DATABASE_PATH = /app/data/database
CMD ["python","main.py"]
