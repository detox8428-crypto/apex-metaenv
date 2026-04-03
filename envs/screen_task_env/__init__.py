"""Screen Task Environment - OpenEnv Environment for GUI Interaction Learning"""

from .models import ScreenAction, ScreenObservation, ScreenState
from .client import ScreenTaskEnvClient

__version__ = "0.1.0"
__all__ = ["ScreenAction", "ScreenObservation", "ScreenState", "ScreenTaskEnvClient"]
