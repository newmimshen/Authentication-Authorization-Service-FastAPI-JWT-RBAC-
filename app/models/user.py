from sqlalchemy import Column, Integer, String, Boolean
from app.config import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")  # user یا admin

    # برای قابلیت‌های ایمیل و ریست رمز
    is_verified = Column(Boolean, default=False)
    refresh_token = Column(String, nullable=True)
    reset_token = Column(String, nullable=True)
    email_verification_token = Column(String, nullable=True)
