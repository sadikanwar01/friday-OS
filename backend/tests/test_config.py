from backend.config import Settings, get_settings


def test_settings_default_values():
    settings = Settings()
    assert settings.app_name == "FRIDAY OS"
    assert settings.api_port == 8000
    assert settings.db_echo is False
    assert settings.security_mode == "confirm"


def test_settings_properties():
    settings = Settings(app_env="development")
    assert settings.is_development is True
    assert settings.is_production is False

    settings_prod = Settings(app_env="production")
    assert settings_prod.is_development is False
    assert settings_prod.is_production is True


def test_get_settings_singleton():
    settings_1 = get_settings()
    settings_2 = get_settings()
    assert settings_1 is settings_2
