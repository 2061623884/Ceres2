"""Disable dotenv reads for isolated real-provider validation subprocesses."""
from app.core.config import Settings, get_settings
Settings.model_config['env_file'] = None
get_settings.cache_clear()
