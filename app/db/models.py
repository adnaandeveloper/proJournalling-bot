from sqlalchemy import Column, Integer, String, BigInteger, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base
class User(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True)
    telegram_id=Column(BigInteger,unique=True,index=True)
    language=Column(String(2),default="da")
    is_active=Column(Integer,default=0)
    created_at=Column(DateTime,default=datetime.utcnow)
class Account(Base):
    __tablename__="accounts"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("users.id"))
    name=Column(String(50))
    type=Column(String(20))
    status=Column(String(20),default="active")
    start_balance=Column(Float,default=0)
    created_at=Column(DateTime,default=datetime.utcnow)
class Pair(Base):
    __tablename__="pairs"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("users.id"))
    symbol=Column(String(20))
class Trade(Base):
    __tablename__="trades"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("users.id"))
    account_id=Column(Integer,ForeignKey("accounts.id"))
    pair_id=Column(Integer,ForeignKey("pairs.id"))
    direction=Column(String(10))
    target_profit=Column(Float)
    risk=Column(Float)
    comment=Column(Text)
    setup_file_id=Column(String(200))
    status=Column(String(10),default="open")
    result=Column(String(10))
    actual_pl=Column(Float)
    close_file_id=Column(String(200))
    close_comment=Column(Text)
    created_at=Column(DateTime,default=datetime.utcnow)
    closed_at=Column(DateTime)
class Cashflow(Base):
    __tablename__="cashflows"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("users.id"))
    account_id=Column(Integer,ForeignKey("accounts.id"))
    type=Column(String(20))
    amount=Column(Float)
    note=Column(Text)
    created_at=Column(DateTime,default=datetime.utcnow)
