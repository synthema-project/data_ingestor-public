import os

class Settings:
    #PostgreSQL settings
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "dataset_catalogue")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER","fcasadei")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD","7IGc540zOTX04ET")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "mstorage-svc")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432") #5432 80

    # MinIO settings
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "obstorageapi.k8s.synthema.rid-intrasoft.eu")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "mqcqwECvoga6pkDRhOUz")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY","EN6t1TWZELRhn1LyGoi6ubtApmXoUJfsny9tRYz9")
    MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "data-annotation")

settings = Settings()


#class Settings:
#    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "task_center")
#    POSTGRES_USER: str = os.getenv("POSTGRES_USER","user")
#    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD","pass")
#    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "192.168.65.158")
#    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432") #5432 80

#settings = Settings()
