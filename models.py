from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    seat_number = Column(String(10), unique=True, index=True)
    
    # 해당 좌석의 모든 예약들
    reservations = relationship("Reservation", back_populates="seat")
    # 해당 좌석에 남겨진 메시지들
    messages = relationship("Message", back_populates="seat")

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    seat_id = Column(Integer, ForeignKey("seats.id"))
    user_name = Column(String(50))
    employee_id = Column(String(20))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.now)

    seat = relationship("Seat", back_populates="reservations")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    seat_id = Column(Integer, ForeignKey("seats.id"))
    sender_name = Column(String(50))
    content = Column(String(200))
    created_at = Column(DateTime, default=datetime.datetime.now)

    seat = relationship("Seat", back_populates="messages")
