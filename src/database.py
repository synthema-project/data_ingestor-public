from sqlmodel import create_engine, SQLModel, Session

#postgres_arg = "postgres:password_prova@localhost:5432/"
#postgres_url = f"postgresql://{postgres_arg}"

#postgres_arg = f"{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
#postgres_url = f"postgresql://{postgres_arg}"

#connect_args = {}
#engine = create_engine(postgres_url, echo=True, connect_args=connect_args)

#def create_db_and_tables():
#    SQLModel.metadata.create_all(engine)

#def get_session():
#    return Session(engine)
