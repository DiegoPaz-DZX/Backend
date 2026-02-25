import datetime
from sqlalchemy import Column, String, Boolean, Integer, Date, Float
from .database import Base

class Usuario(Base):
    __tablename__ = "pw_users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    createdtime = Column(Date, default=lambda: datetime.date.today())
    emailverified = Column(Boolean, default=False)
    userrole = Column(String, default="USER")

class Gasto(Base):
    __tablename__ = "pw_job"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(Date, nullable=False)
    mount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, nullable=False)

class Presupuesto(Base):
    __tablename__ = "pw_presupuesto"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category = Column(String, nullable=False, default="TOTAL")
    limit_mount = Column(Float, nullable=False)
    month_year = Column(String, nullable=False)