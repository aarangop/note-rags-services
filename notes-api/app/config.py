from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")


config = Config()


def get_config(reset: bool = False) -> Config:
    global config
    if not config or (config and reset):
        config = Config()

    return config


def reset_config():
    global config
    config = Config()
