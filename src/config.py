import os

class Settings:
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "dataset_catalogue")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER","fcasadei")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD","7IGc540zOTX04ET")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "mstorage-svc")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432") #5432 80

settings = Settings()
