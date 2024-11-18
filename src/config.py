import os

#class Settings:
#    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "dataset_catalogue")
#    POSTGRES_USER: str = os.getenv("POSTGRES_USER","fcasadei")
#    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD","7IGc540zOTX04ET")
#    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "mstorage-svc")
#    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432") #5432 80

#settings = Settings()


class Settings:
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "task_center")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER","user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD","pass")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "192.168.65.158")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432") #5432 80

settings = Settings()
