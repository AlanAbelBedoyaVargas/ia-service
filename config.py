"""Configuración del servicio de IA.

Las variables se leen del archivo .env (ver .env.example). Nunca se
codifican credenciales en el código fuente.
"""

from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Proveedor de IA (Google Gemini)
    ai_api_key: str = ""
    ai_model: str = "gemini-2.5-flash-lite"

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
