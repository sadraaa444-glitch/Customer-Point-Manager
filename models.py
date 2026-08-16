from datetime import date
from typing import List, Optional
from sqlalchemy import String, Integer, Date, ForeignKey, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum
from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

class Base(DeclarativeBase):
    pass

class TransactionType(str, enum.Enum):
    EARN = "earn"       
    REDEEM = "redeem"   
    LOAN = "loan"       

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    created_at: Mapped[date] = mapped_column(Date, default=date.today)
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Customer(name={self.name})>"

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    transaction_type: Mapped[TransactionType]
    reference_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) 
    transaction_date: Mapped[date] = mapped_column(Date, default=date.today)
    points: Mapped[int] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


    customer: Mapped["Customer"] = relationship(back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction(points={self.points}, date={self.transaction_date})>"