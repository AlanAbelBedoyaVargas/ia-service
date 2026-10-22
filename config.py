"""Configuración del servicio de IA.

Las variables se leen del archivo .env (ver .env.example). Nunca se
codifican credenciales en el código fuente.
"""

from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# El .env vive junto a este archivo. Además de cargarlo en los Settings de
# abajo, se carga al entorno del PROCESO: así las librerías que leen
# variables de entorno directamente (por ejemplo LangSmith con
# LANGSMITH_TRACING / LANGSMITH_API_KEY) también las ven sin tocar código.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    # Proveedor de IA vía OpenRouter: API compatible con el formato de
    # OpenAI que expone modelos de Google, OpenAI, Anthropic, etc.
    # AI_MODEL usa el slug de OpenRouter con prefijo de proveedor.
    ai_api_key: str = ""
    ai_base_url: str = "https://openrouter.ai/api/v1"
    ai_model: str = "google/gemini-3.5-flash-lite"

    # Base de datos (SOLO lectura de la tabla alimentos; mismas variables que el backend)
    db_username: str = ""
    db_password: str = ""
    db_name: str = ""
    db_host: str = "localhost"
    db_port: int = 5432

    # Clave compartida con el backend para la comunicación interna
    ia_internal_key: str = ""

    # Puerto del servidor
    port: int = 8000

    @property
    def database_url(self) -> str:
        """Cadena de conexión SQLAlchemy para PostgreSQL (psycopg2)."""
        usuario = quote_plus(self.db_username)
        contrasenia = quote_plus(self.db_password)
        return (
            f"postgresql+psycopg2://{usuario}:{contrasenia}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
