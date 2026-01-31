import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

APP_NAME = os.environ.get("APP_NAME", "Fraud Forge API")
APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")
DEBUG_MODE = os.environ.get("DEBUG", "false").lower() == "true"
API_PREFIX = os.environ.get("API_PREFIX", "/api")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "default_secret")
JWT_ALGORITHM = "HS256"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

RSB_STORAGE_DIR = ROOT_DIR / "data" / "rsb_packages"
RSB_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

TRACE_ROOT = ROOT_DIR / "run_artifacts"
