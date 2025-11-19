from fastapi import FastAPI
from app.config import Base, engine
from app.models import user
from app.routes import auth

# ساخت اپ
app = FastAPI(
    title="Auth Project",
    description="سیستم احراز هویت کامل با JWT، Refresh Token، RBAC و ایمیل",
    version="1.0.0",
)

# ساخت جداول دیتابیس
Base.metadata.create_all(bind=engine)

# اضافه کردن روت‌های Auth
app.include_router(auth.router, prefix="/auth", tags=["auth"])

# روت ساده برای تست
@app.get("/")
def read_root():
    return {"message": "Auth Project is running!"}
