from PyQt5.QtCore import QSettings

def load_settings():
    settings = QSettings("ChatDot", "ChatDotApp")
    api_key = settings.value("api_key", "")
    model_name = settings.value("model_name", "default_model")
    return {
        "api_key": api_key,
        "model_name": model_name,
    }

def save_settings(api_key, model_name):
    settings = QSettings("ChatDot", "ChatDotApp")
    settings.setValue("api_key", api_key)
    settings.setValue("model_name", model_name)