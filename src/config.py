import os


def get_env_variable(name: str) -> str:
    """Fetches an environment variable and raises an exception if it's missing."""
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _get_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


class Settings:
    # PostgreSQL (shared with the data-catalogue: same DB/tables)
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "dataset_catalogue")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "appuser")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "apppassword")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    # MinIO / object storage (where dataset bytes are uploaded by this ingestor)
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio.synthema.svc.cluster.local:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME", "data-annotation")
    MINIO_SECURE: bool = _get_bool("MINIO_SECURE", False)

    # This ingestor instance's node/org name (prod: one ingestor per org).
    NODE_NAME: str = os.getenv("NODE_NAME", "NODE1")

    # Downstream services
    CATALOGUE_ENDPOINT: str = os.getenv(
        "CATALOGUE_ENDPOINT", "http://data-catalogue-service:83/metadata"
    )
    ANNOTATION_ENDPOINT: str = os.getenv(
        "ANNOTATION_ENDPOINT", "http://data-annotation-service:80/schema"
    )
    # Optional bearer token forwarded to the (Keycloak-protected) catalogue.
    CATALOGUE_TOKEN: str = os.getenv("CATALOGUE_TOKEN", "")

    # HTTP server port
    APP_PORT: int = int(os.getenv("APP_PORT", "82"))


settings = Settings()

# Keycloak (auth). Defaults preserve the previously hardcoded values.
KEYCLOAK_SERVER_URL: str = os.getenv(
    "KEYCLOAK_SERVER_URL", "https://users.k8s.synthema.rid-intrasoft.eu"
)
KEYCLOAK_CLIENT_ID: str = os.getenv("KEYCLOAK_CLIENT_ID", "synthema")
KEYCLOAK_REALM_NAME: str = os.getenv("KEYCLOAK_REALM_NAME", "Synthema")
