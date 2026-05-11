from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
import models, database
from database import engine, get_db
import datetime
from typing import List, Optional
from pydantic import BaseModel

# DB 테이블 생성
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="자율좌석 예약 봇 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 모델
class ReservationCreate(BaseModel):
    user_name: str
    employee_id: str
    start_time: datetime.datetime
    end_time: datetime.datetime

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

@app.get("/seats")
def get_seats(db: Session = Depends(get_db)):
    # 오늘 날짜의 예약들만 가져오기 위해 필터링하거나, 전체를 가져와서 프론트에서 처리
    # 여기서는 성능을 위해 오늘 날짜 기준 예약을 포함하여 가져옴
    today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + datetime.timedelta(days=1)
    
    seats = db.query(models.Seat).options(
        joinedload(models.Seat.reservations)
    ).all()
    
    # 각 좌석별로 현재 시각 기준 예약 상태를 계산하여 반환
    now = datetime.datetime.now()
    result = []
    for seat in seats:
        active_res = next((r for r in seat.reservations if r.start_time <= now <= r.end_time), None)
        result.append({
            "id": seat.id,
            "seat_number": seat.seat_number,
            "current_reservation": active_res,
            "all_reservations": sorted(seat.reservations, key=lambda x: x.start_time)
        })
    return result

@app.post("/reserve/{seat_id}")
def reserve_seat(seat_id: int, res_data: ReservationCreate, db: Session = Depends(get_db)):
    # 1. 좌석 존재 확인
    seat = db.query(models.Seat).filter(models.Seat.id == seat_id).first()
    if not seat:
        raise HTTPException(status_code=404, detail="좌석을 찾을 수 없습니다.")
    
    # 2. 시간 유효성 확인
    if res_data.start_time >= res_data.end_time:
        raise HTTPException(status_code=400, detail="시작 시간은 종료 시간보다 빨라야 합니다.")
    
    # 3. 중복 예약(오버랩) 확인
    overlap = db.query(models.Reservation).filter(
        models.Reservation.seat_id == seat_id,
        models.Reservation.start_time < res_data.end_time,
        models.Reservation.end_time > res_data.start_time
    ).first()
    
    if overlap:
        raise HTTPException(status_code=400, detail=f"해당 시간대({overlap.start_time.strftime('%H:%M')}~{overlap.end_time.strftime('%H:%M')})에 이미 예약이 있습니다.")

    # 4. 예약 생성
    new_res = models.Reservation(
        seat_id=seat_id,
        user_name=res_data.user_name,
        employee_id=res_data.employee_id,
        start_time=res_data.start_time,
        end_time=res_data.end_time
    )
    db.add(new_res)
    db.commit()
    return {"message": "예약 성공", "reservation": new_res}

@app.delete("/reservations/{res_id}")
def cancel_reservation(res_id: int, db: Session = Depends(get_db)):
    res = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="예약을 찾을 수 없습니다.")
    
    db.delete(res)
    db.commit()
    return {"message": "예약 취소 완료"}

@app.get("/")
def read_index():
    return FileResponse("static/index.html")
