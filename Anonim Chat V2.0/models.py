from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# Kullanıcı tablosu
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)  # görünür ID
    username = Column(String)
    password_hash = Column(String)

# Eşleşme odaları
class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String, unique=True, index=True)
    user1_id = Column(String, ForeignKey("users.user_id"))
    user2_id = Column(String, ForeignKey("users.user_id"))
    created_at = Column(DateTime, default=datetime.utcnow)
