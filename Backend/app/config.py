"""
Reads the .env file into Python so the rest of the app can use settings.database_url,
settings.secret_key, etc. instead of every file reading .env on its own.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    groq_api_key: str = ""
    # Secret codeword required to register as an "official" (Gram Panchayat officer)
    # account. Only people who know this can create an official login.
    official_registration_code: str = "CHANGE_ME"
    # Secret verification code required to register as an ASHA healthcare worker (provided by PHC)
    asha_registration_code: str = "ASHA2026"

    class Config:
        env_file = ".env"


settings = Settings()
