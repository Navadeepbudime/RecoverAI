import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "recoverai-dev-only")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///recoverai_demo.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

    # Payment provider: "demo" (default, no API keys) or "razorpay" (future)
    PAYMENT_PROVIDER = os.getenv("PAYMENT_PROVIDER", "demo")

    # Gemini or another LLM provider (optional — demo agent works without it)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # Razorpay credentials — only needed when PAYMENT_PROVIDER=razorpay
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
    RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
