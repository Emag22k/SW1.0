from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///battleship.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

Base = declarative_base()

class GameResult(Base):
    __tablename__ = "game_results"

    id = Column(Integer, primary_key=True, index=True)
    winner = Column(String, nullable=False)
    moves = Column(Integer, nullable=False)

Base.metadata.create_all(engine)

def get_all_results():
    return session.query(GameResult).all()

