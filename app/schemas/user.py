from pydantic import BaseModel

# ورودی برای ثبت‌نام و لاگین
class UserCreate(BaseModel):
    email: str
    password: str

# خروجی برای نمایش اطلاعات کاربر
class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    role: str
    is_verified: bool

    class Config:
        orm_mode = True

# خروجی برای توکن‌ها
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

# ورودی برای درخواست ریست رمز (با ایمیل)
class PasswordResetRequest(BaseModel):
    email: str

# ورودی برای ست کردن رمز جدید از طریق توکن
class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
