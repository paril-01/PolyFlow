"""Service configuration."""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/recommendation_python")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SERVICE_PORT = 8086
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
