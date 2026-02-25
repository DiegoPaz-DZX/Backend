from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

#CADENA_CONEXION = "postgresql://pw_trabajo:trabajo@localhost:5432/pw_trabajo"
CADENA_CONEXION = "postgresql://appfinanzas_db_user:ZBA0y52MY9T5GXNskOg7iIafgyah2OYt@dpg-d6f73pogjchc73fi0ef0-a.oregon-postgres.render.com/appfinanzas_db"

engine = create_engine(CADENA_CONEXION)
session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()