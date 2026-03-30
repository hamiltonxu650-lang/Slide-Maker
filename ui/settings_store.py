from __future__ import annotations

import json

from PyQt6 import QtCore

from services.app_models import (
    APP_BRAND,
    SETTINGS_APP,
    SETTINGS_ORG,
    AppSettings,
    TaskPreferences,
)


def _settings() -> QtCore.QSettings:
    return QtCore.QSettings(SETTINGS_ORG, SETTINGS_APP)


def load_app_settings() -> AppSettings:
    settings = _settings()
    payload = {}
    for key, default in AppSettings().to_dict().items():
        value = settings.value(f"app/{key}", default)
        if isinstance(default, bool):
            payload[key] = _as_bool(value, default)
        elif isinstance(default, int):
            payload[key] = int(value)
        else:
            payload[key] = value
    return AppSettings.from_dict(payload)


def save_app_settings(app_settings: AppSettings) -> None:
    settings = _settings()
    for key, value in app_settings.to_dict().items():
        settings.setValue(f"app/{key}", value)
    settings.sync()


def reset_app_settings() -> AppSettings:
    defaults = AppSettings()
    save_app_settings(defaults)
    return defaults


def load_last_preferences() -> TaskPreferences:
    settings = _settings()
    raw = settings.value("task/last_preferences", "")
    if not raw:
        return TaskPreferences()
    try:
        return TaskPreferences.from_dict(json.loads(str(raw)))
    except json.JSONDecodeError:
        return TaskPreferences()


def save_last_preferences(preferences: TaskPreferences) -> None:
    settings = _settings()
    settings.setValue("task/last_preferences", json.dumps(preferences.to_dict(), ensure_ascii=False))
    settings.sync()


def load_recent_tasks() -> list[str]:
    settings = _settings()
    raw = settings.value("recent/tasks", "")
    if not raw:
        return []
    try:
        data = json.loads(str(raw))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [str(item) for item in data if str(item).strip()]


def save_recent_tasks(tasks: list[str]) -> None:
    settings = _settings()
    settings.setValue("recent/tasks", json.dumps(list(tasks), ensure_ascii=False))
    settings.sync()


def clear_recent_tasks() -> None:
    settings = _settings()
    settings.remove("recent/tasks")
    settings.sync()


def app_brand() -> str:
    return APP_BRAND


def _as_bool(value, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
