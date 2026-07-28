import os

def load_env_vars():
    """Load environment variables from .env file if running outside Docker container."""
    if not os.getenv("ACCESS_TOKEN") and os.path.exists(".env"):
        try:
            with open(".env") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ.setdefault(key.strip(), value.strip().strip("'\""))
        except Exception:
            pass

def get_required_access_token() -> str:
    """Return the configured access token or empty string if not required."""
    load_env_vars()
    return os.getenv("ACCESS_TOKEN", "").strip()

def verify_token(user_input: str) -> bool:
    """Verify if the user provided token matches the environment ACCESS_TOKEN."""
    required_token = get_required_access_token()
    if not required_token:
        return True
    return bool(user_input and user_input.strip() == required_token)
