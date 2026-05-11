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

class MessageCreate(BaseModel):
    sender_name: str
    content: str

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
    seats = db.query(models.Seat).options(
        joinedload(models.Seat.reservations),
        joinedload(models.Seat.messages)
    ).order_by(models.Seat.seat_number).all()
    
    now = datetime.datetime.now()
    result = []
    for seat in seats:
        active_res = next((r for r in seat.reservations if r.start_time <= now <= r.end_time), None)
        result.append({
            "id": seat.id,
            "seat_number": seat.seat_number,
            "current_reservation": active_res,
            "all_reservations": sorted(seat.reservations, key=lambda x: x.start_time),
            "messages": sorted(seat.messages, key=lambda x: x.created_at, reverse=True)
        })
    return result

@app.post("/reserve/{seat_id}")
def reserve_seat(seat_id: int, res_data: ReservationCreate, db: Session = Depends(get_db)):
    seat = db.query(models.Seat).filter(models.Seat.id == seat_id).first()
    if not seat:
        raise HTTPException(status_code=404, detail="좌석을 찾을 수 없습니다.")
    
    if res_data.start_time >= res_data.end_time:
        raise HTTPException(status_code=400, detail="시작 시간은 종료 시간보다 빨라야 합니다.")
    
    overlap = db.query(models.Reservation).filter(
        models.Reservation.seat_id == seat_id,
        models.Reservation.start_time < res_data.end_time,
        models.Reservation.end_time > res_data.start_time
    ).first()
    
    if overlap:
        raise HTTPException(status_code=400, detail=f"해당 시간대({overlap.start_time.strftime('%H:%M')}~{overlap.end_time.strftime('%H:%M')})에 이미 예약이 있습니다.")

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

@app.post("/seats/{seat_id}/messages")
def post_message(seat_id: int, msg_data: MessageCreate, db: Session = Depends(get_db)):
    new_msg = models.Message(
        seat_id=seat_id,
        sender_name=msg_data.sender_name,
        content=msg_data.content
    )
    db.add(new_msg)
    db.commit()
    return new_msg

@app.delete("/messages/{message_id}")
def delete_message(message_id: int, db: Session = Depends(get_db)):
    msg = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="메시지를 찾을 수 없습니다.")
    db.delete(msg)
    db.commit()
    return {"message": "메시지 삭제 완료"}

@app.get("/")
def read_index():
    return FileResponse("static/index.html")
