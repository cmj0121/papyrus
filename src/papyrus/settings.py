"""The global settings of Papyrus"""
import enum

from pydantic import BaseSettings
from pydantic import Field


PROJ_NAME = "papyrus"


class LogLevel(enum.Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class Settings(BaseSettings):
    """The global settings of Papyrus, which controls the behavior of Papyrus."""""

    DEBUG: bool = Field(default=False, description="used to enable or disable the debug mode")
    LOG_LEVEL: LogLevel = Field(default=LogLevel.ERROR, description="the log level of Papyrus")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
