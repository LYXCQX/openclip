"""
Configuration file for LLM clients and other components
"""

from typing import Dict, Any


# LLM Client configurations
LLM_CONFIG: Dict[str, Dict[str, Any]] = {
    "qwen": {
        # New models (qwen3.5, qwen3, etc.) use OpenAI-compatible endpoint
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        # Old models (qwen-turbo, qwen-plus, qwen-max) use DashScope endpoint
        "legacy_base_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
        "default_model": "qwen3.5-flash",
        "default_params": {
            "max_tokens": 16384,
            "temperature": 0.7,
            "top_p": 0.8,
            "stream": False
        },
        # Models that use the legacy endpoint
        "legacy_models": ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-long"]
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "default_model": "stepfun/step-3.5-flash:free",
        "default_params": {
            "max_tokens": 32768,
            "temperature": 0.7,
            "top_p": 0.8,
            "stream": False
        }
    }
}


# Environment variable names for API keys
API_KEY_ENV_VARS: Dict[str, str] = {
    "qwen": "QWEN_API_KEY",
    "openrouter": "OPENROUTER_API_KEY"
}


# Default LLM provider
DEFAULT_LLM_PROVIDER: str = "qwen"

# Video splitting
MAX_DURATION_MINUTES: float = 20.0

# Whisper model for transcript generation
# Options: tiny, base, small, medium, large, turbo
WHISPER_MODEL: str = "small"

# Use WhisperX by default (better timestamp alignment and optional speaker diarization)
# Set to False to use standard Whisper instead
USE_WHISPERX_BY_DEFAULT: bool = True

# Use character-level alignment in WhisperX for maximum precision
# Character-level provides ~50-200ms precision vs word-level ~100-500ms
# Recommended for better sentence boundary detection
USE_CHAR_LEVEL_ALIGNMENT: bool = False

# Title style for artistic text overlay
# Options: gradient_3d, neon_glow, metallic_gold, rainbow_3d, crystal_ice,
#          fire_flame, metallic_silver, glowing_plasma, stone_carved, glass_transparent
DEFAULT_TITLE_STYLE: str = "fire_flame"

# Maximum number of highlight clips to generate
MAX_CLIPS: int = 5

# Skip download by default (use existing files if available)
SKIP_DOWNLOAD: bool = False

# Skip transcript generation (use existing transcript files if available)
SKIP_TRANSCRIPT: bool = False

# Sentence boundary adjustment for clips
# Automatically adjust clip start/end times to align with complete sentences
ENABLE_SENTENCE_ADJUSTMENT: bool = True

# Maximum seconds to extend clip boundaries to find sentence endings
MAX_SENTENCE_EXTENSION: float = 5.0
