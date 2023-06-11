"""The global settings of Papyrus"""
from pydantic import Field
from pydantic_yaml import YamlModel
from pydantic_yaml import YamlStrEnum


PROJ_NAME = "papyrus"


class LogLevel(YamlStrEnum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class LayerSettings(YamlModel):
    name: str | None = Field(default=None, description="the name of the layer")
    uri: str = Field(..., description="the uri of the layer")
    threshold: int | None = Field(default=None, description="the threshold of the layer")


class Settings(YamlModel):
    """The global settings of Papyrus, which controls the behavior of Papyrus."""""

    debug: bool = Field(default=False, description="used to enable or disable the debug mode")
    log_level: LogLevel = Field(default=LogLevel.ERROR, description="the log level of Papyrus")

    layers: list[LayerSettings] = Field(..., description="the layers of Papyrus")

    class Config:
        env_file = ".env.yml .env.yaml"
        env_file_encoding = "utf-8"
