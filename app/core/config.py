import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL Database Configuration
# DATABASE_URL 형식: postgresql://user:password@host:port/database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/egoeng_db"
)

# Database connection settings (필요시 개별 설정 사용)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "egoeng_db")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root1234")

# DATABASE_URL이 없으면 개별 설정으로 조합
if DATABASE_URL == "postgresql://postgres:postgres@localhost:5432/egoeng_db" and os.getenv("DATABASE_URL") is None:
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# pgvector settings
VECTOR_DIMENSION = 1536  # OpenAI embedding dimension (text-embedding-ada-002 or text-embedding-3-small)

