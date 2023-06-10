"""The global settings of Papyrus"""
import enum

from pydantic import Field
from pydantic_yaml import YamlModel


PROJ_NAME = "papyrus"


class LogLevel(enum.Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class Settings(YamlModel):
    """The global settings of Papyrus, which controls the behavior of Papyrus."""""

    debug: bool = Field(default=False, description="used to enable or disable the debug mode")
    log_level: LogLevel = Field(default=LogLevel.ERROR, description="the log level of Papyrus")

    layers: list[str] = Field(..., description="the layers of Papyrus")

    class Config:
        env_file = ".env.yml .env.yaml"
        env_file_encoding = "utf-8"
