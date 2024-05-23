FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11-slim
WORKDIR /app
RUN mkdir data
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r ./requirements.txt
COPY . .
EXPOSE 8002
ENV DATASET_PATH = /app/data/dataset
CMD ["python","main.py"]
