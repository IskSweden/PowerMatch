from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from datetime import timezone

Base = declarative_base()

class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    difficulty = Column(String, nullable=False)
    seed = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
