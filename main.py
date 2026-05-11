from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import models, database
from database import engine, get_db
import datetime
import os

# DB 테이블 생성
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="자율좌석 예약 봇 API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 초기 좌석 데이터 (20개) 생성 함수
def init_seats():
    db = database.SessionLocal()
    if db.query(models.Seat).count() == 0:
        for i in range(1, 21):
            seat = models.Seat(seat_number=f"{i:02d}번")
            db.add(seat)
        db.commit()
    db.close()

@app.on_event("startup")
def startup_event():
    init_seats()

# API 엔드포인트들
@app.get("/seats")
def get_seats(db: Session = Depends(get_db)):
    return db.query(models.Seat).all()

@app.post("/reserve/{seat_id}")
def reserve_seat(seat_id: int, user_name: str, employee_id: str, db: Session = Depends(get_db)):
    seat = db.query(models.Seat).filter(models.Seat.id == seat_id).first()
    if not seat:
        raise HTTPException(status_code=404, detail="좌석을 찾을 수 없습니다.")
    if seat.is_reserved:
        raise HTTPException(status_code=400, detail="이미 예약된 좌석입니다.")
    
    seat.is_reserved = True
    seat.reserved_by = user_name
    seat.employee_id = employee_id
    seat.reserved_at = datetime.datetime.now()
    # 기본 8시간 후 만료로 설정 (곧 비는 자리 예시를 위해)
    seat.expires_at = datetime.datetime.now() + datetime.timedelta(hours=8)
    db.commit()
    return {"message": f"{seat.seat_number} 좌석 예약 완료", "seat": seat}

@app.post("/cancel/{seat_id}")
def cancel_reservation(seat_id: int, db: Session = Depends(get_db)):
    seat = db.query(models.Seat).filter(models.Seat.id == seat_id).first()
    if not seat:
        raise HTTPException(status_code=404, detail="좌석을 찾을 수 없습니다.")
    
    seat.is_reserved = False
    seat.reserved_by = None
    seat.employee_id = None
    seat.reserved_at = None
    seat.expires_at = None
    db.commit()
    return {"message": f"{seat.seat_number} 예약 취소 완료"}

# 프론트엔드 정적 파일 서빙 (맨 아래에 위치해야 함)
@app.get("/")
def read_index():
    return FileResponse("static/index.html")
