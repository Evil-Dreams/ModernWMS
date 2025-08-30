import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "modernwms")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

JWT_SECRET = os.getenv("JWT_SECRET", "ChangeThisSecretKey")
JWT_ISSUER = os.getenv("JWT_ISSUER", "ModernWMS.Py")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "ModernWMS.Client")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

APP_PORT = int(os.getenv("APP_PORT", "5555"))

ENC_USER = quote_plus(POSTGRES_USER)
ENC_PASS = quote_plus(POSTGRES_PASSWORD)
DATABASE_URL = (
    f"postgresql+psycopg2://{ENC_USER}:{ENC_PASS}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
