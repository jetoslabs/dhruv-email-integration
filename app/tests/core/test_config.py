from app.core.config import Config


def test_validate_and_load():
    config = Config().validate_and_load("../configuration")
    assert config.system_configuration.tenant == "SYSTEM"
