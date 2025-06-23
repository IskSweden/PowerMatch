from fastapi import APIRouter
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..db import SessionLocal
from ..models.score import Score

router = APIRouter()

@router.get("/api/highscores")
def get_highscores():
    db: Session = SessionLocal()

    now = datetime.utcnow()
    day_ago = now - timedelta(hours=24)

    alltime = db.query(Score).order_by(Score.score.desc()).limit(5).all()
    recent = db.query(Score).filter(Score.timestamp >= day_ago).order_by(Score.score.desc()).limit(5).all()

    def to_dict(score):
        return {
            "name": score.name,
            "score": round(score.score, 2),
            "difficulty": score.difficulty,
            "timestamp": score.timestamp.isoformat()
        }

    return {
        "alltime": [to_dict(s) for s in alltime],
        "recent": [to_dict(s) for s in recent]
    }
