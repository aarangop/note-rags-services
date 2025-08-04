from auth_lib.jwt_service import JWTServiceBuilder
from fastapi import Depends

from app.config import Config, get_config


def get_jwt_service(config: Config = Depends(get_config)):
    builder = JWTServiceBuilder()
    (
        builder.set_jwt_access_token_expire_minutes(config.jwt_access_token_expire_minutes)
        .set_jwt_algorithm(config.jwt_algorithm)
        .set_jwt_refresh_token_expire_days(config.jwt_refresh_token_expire_days)
    )
    if config.private_key_path:
        builder.set_private_key_path(config.private_key_path)
    if config.public_key_path:
        builder.set_public_key_path(config.public_key_path)
    return builder.build()
