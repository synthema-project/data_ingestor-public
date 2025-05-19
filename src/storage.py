from minio import Minio
from config import settings

# Initialize MinIO client
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=True  # Change to True if using HTTPS
)

# Ensure the bucket exists
def ensure_bucket():
    print(f"Bucket name: '{settings.MINIO_BUCKET_NAME}'")
    if not minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
        minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
        print(f"Bucket '{settings.MINIO_BUCKET_NAME}' created successfully.")
    else:
        print(f"Bucket '{settings.MINIO_BUCKET_NAME}' already exists.")

ensure_bucket()

# Function to upload a file
def upload_file(file_path: str, object_name: str):
    minio_client.fput_object(settings.MINIO_BUCKET_NAME, object_name, file_path)
    print(f"File '{file_path}' uploaded as '{object_name}' in bucket '{settings.MINIO_BUCKET_NAME}'.")

# Function to download a file
def download_file(object_name: str, file_path: str):
    minio_client.fget_object(settings.MINIO_BUCKET_NAME, object_name, file_path)
    print(f"File '{object_name}' downloaded to '{file_path}'.")
