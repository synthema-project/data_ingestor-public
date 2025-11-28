import os

def get_env_variable(name: str) -> str:
    """Fetches an environment variable and raises an exception if it's missing."""
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"Missing required environment variable: {name}")
    return value

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

# Keycloak
KEYCLOAK_SERVER_URL="https://users.k8s.synthema.rid-intrasoft.eu"#os.getenv("KEYCLOAK_SERVER_URL", "https://users.k8s.synthema.rid-intrasoft.eu" )
KEYCLOAK_CLIENT_ID="synthema"#os.getenv("KEYCLOAK_CLIENT_ID", "synthema")
KEYCLOAK_REALM_NAME="Synthema"#os.getenv("KEYCLOAK_REALM", "Synthema")
#KEYCLOAK_SERVER_URL = get_env_variable("KEYCLOAK_SERVER_URL")
#KEYCLOAK_CLIENT_ID = get_env_variable("KEYCLOAK_CLIENT_ID")
#KEYCLOAK_CLIENT_SECRET = get_env_variable("KEYCLOAK_CLIENT_SECRET")
#KEYCLOAK_REALM_NAME = get_env_variable("KEYCLOAK_REALM_NAME")
#KEYCLOAK_REDIRECT_URI = get_env_variable("KEYCLOAK_REDIRECT_URI")
#KEYCLOAK_AUTHORIZED_ROLE = get_env_variable("KEYCLOAK_AUTHORIZED_ROLE")
#KEYCLOAK_AUTHORIZED_GROUP = get_env_variable("KEYCLOAK_AUTHORIZED_GROUP") # Keycloak uses `/` prefix for group paths
#KEYCLOAK_ROLE_NAME_PLATFORM_ADMIN = get_env_variable("KEYCLOAK_ROLE_NAME_PLATFORM_ADMIN")
#KEYCLOAK_ROLE_NAME_ML_RESEARCHER = "MLResearcher"


#class Settings:
#    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "task_center")
#    POSTGRES_USER: str = os.getenv("POSTGRES_USER","user")
#    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD","pass")
#    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "192.168.65.158")
#    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432") #5432 80

#settings = Settings()
