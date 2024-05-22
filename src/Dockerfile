FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11-slim
WORKDIR /app
RUN mkdir data
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r ./requirements.txt
COPY . .
EXPOSE 8003
CMD ["python","main.py"]
