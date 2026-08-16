from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Customer, Transaction, TransactionType
from datetime import date
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()
    
def create_admin_if_not_exists(db: Session):
    admin = get_user_by_username(db, "admin")
    if not admin:
        initial_password = os.getenv("ADMIN_INIT_PASSWORD")
        if not initial_password:
            raise ValueError("متغیر محیطی ADMIN_INIT_PASSWORD تنظیم نشده است!")
            
        hashed_pwd = get_password_hash(initial_password)
        admin_user = models.User(username="admin", hashed_password=hashed_pwd)
        db.add(admin_user)
        db.commit()

def create_customer(db: Session, name: str, phone: str = None) -> Customer:
    db_customer = Customer(name=name, phone=phone)
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def get_customers_with_balance(db: Session):
    results = db.query(
        Customer,
        func.coalesce(func.sum(Transaction.points), 0).label('total_points')
    ).outerjoin(Transaction, Customer.id == Transaction.customer_id) \
     .group_by(Customer.id) \
     .order_by(Customer.id.desc()).all()
    return results

def get_customer_by_id(db: Session, customer_id: int):
    """پیدا کردن یک مشتری با ID"""
    return db.query(Customer).filter(Customer.id == customer_id).first()

def get_customer_transactions(db: Session, customer_id: int):
    """دریافت تمام تراکنش‌های یک مشتری به ترتیب تاریخ نزولی"""
    return db.query(Transaction)\
             .filter(Transaction.customer_id == customer_id)\
             .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())\
             .all()

def add_transaction(db: Session, customer_id: int, tx_type: TransactionType, 
                    points: int, ref_number: str = None, desc: str = None, 
                    tx_date: date = None) -> Transaction:
    actual_points = abs(points) if tx_type == TransactionType.EARN else -abs(points)
    
    db_tx = Transaction(
        customer_id=customer_id,
        transaction_type=tx_type,
        points=actual_points,
        reference_number=ref_number,
        description=desc,
        transaction_date=tx_date or date.today()
    )
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)
    return db_tx