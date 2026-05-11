from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database import Base
import datetime

class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    seat_number = Column(String(10), unique=True, index=True)
    is_reserved = Column(Boolean, default=False)
    reserved_by = Column(String(50), nullable=True)
    employee_id = Column(String(20), nullable=True)
    reserved_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True) # 곧 비는 자리를 판단하기 위해 만료 시간 추가
