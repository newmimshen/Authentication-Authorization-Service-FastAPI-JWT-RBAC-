from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from datetime import timedelta
from app.config import SessionLocal
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserResponse, TokenResponse,
    PasswordResetRequest, PasswordResetConfirm
)
from app.utils.security import (
    hash_password, verify_password, create_access_token, decode_access_token
)
from app.utils.email import send_email, build_reset_email, build_verification_email

router = APIRouter()

# Dependency برای گرفتن session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ثبت‌نام کاربر + ارسال ایمیل تأیید
@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.password)
    new_user = User(email=user.email, hashed_password=hashed_pw, is_verified=False)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # ساخت توکن تأیید ایمیل (اعتبار 24 ساعت)
    email_token = create_access_token({"sub": new_user.email, "scope": "verify"}, expires_delta=timedelta(hours=24))
    new_user.email_verification_token = email_token
    db.commit()

    # ارسال ایمیل تأیید (لینک فرانت یا بک)
    verify_link = f"https://your-frontend.example.com/verify-email?token={email_token}"
    html_body = build_verification_email(verify_link)
    try:
        send_email(new_user.email, "Verify your email", html_body)
    except Exception:
        # در محیط توسعه اگر SMTP نداری، فقط ادامه بده
        pass

    return new_user

# ورود کاربر
@router.post("/login", response_model=TokenResponse)
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not db_user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    access_token = create_access_token({"sub": db_user.email, "scope": "access"}, expires_delta=timedelta(minutes=30))
    refresh_token = create_access_token({"sub": db_user.email, "scope": "refresh"}, expires_delta=timedelta(days=7))

    db_user.refresh_token = refresh_token
    db.commit()

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

# OAuth2 برای گرفتن توکن
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# گرفتن کاربر فعلی از Access Token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if payload is None or payload.get("scope") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email: str = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Protected Route
@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Refresh Token
@router.post("/refresh")
def refresh_token(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token found")

    payload = decode_access_token(current_user.refresh_token)
    if payload is None or payload.get("scope") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = create_access_token({"sub": current_user.email, "scope": "access"}, expires_delta=timedelta(minutes=30))
    return {"access_token": new_access_token, "token_type": "bearer"}

# Logout
@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.refresh_token = None
    db.commit()
    return {"message": "Successfully logged out"}

# کنترل نقش‌ها (RBAC)
def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return current_user

@router.get("/admin-only")
def admin_dashboard(current_user: User = Depends(require_admin)):
    return {"message": f"Welcome Admin {current_user.email}"}

# درخواست ریست رمز (ارسال ایمیل با لینک)
@router.post("/request-reset")
def request_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # به‌دلایل امنیتی می‌تونی همیشه پیام موفقیت بدهی؛ اینجا شفاف گفتیم
        raise HTTPException(status_code=404, detail="User not found")

    reset_token = create_access_token({"sub": user.email, "scope": "reset"}, expires_delta=timedelta(minutes=15))
    user.reset_token = reset_token
    db.commit()

    reset_link = f"https://your-frontend.example.com/reset-password?token={reset_token}"
    html_body = build_reset_email(reset_link)
    try:
        send_email(user.email, "Reset your password", html_body)
    except Exception:
        pass

    return {"message": "Password reset link sent to email"}

# تأیید رمز جدید با توکن
@router.post("/reset-password")
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    token = payload.token
    new_password = payload.new_password

    decoded = decode_access_token(token)
    if decoded is None or decoded.get("scope") != "reset":
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    email = decoded.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user or user.reset_token != token:
        raise HTTPException(status_code=400, detail="Invalid reset request")

    user.hashed_password = hash_password(new_password)
    user.reset_token = None
    db.commit()
    return {"message": "Password updated successfully"}

# تأیید ایمیل با توکن
@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    decoded = decode_access_token(token)
    if decoded is None or decoded.get("scope") != "verify":
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    email = decoded.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user or user.email_verification_token != token:
        raise HTTPException(status_code=400, detail="Invalid verification request")

    user.is_verified = True
    user.email_verification_token = None
    db.commit()
    return {"message": "Email verified successfully"}
