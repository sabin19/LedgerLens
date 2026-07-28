import os

DEFAULT_ACCESS_TOKEN = "1ac3111181d1806767d5f1bfd07b5142d48911d48b3c6b4d7bf5bd98930a35a0"

def load_env_vars():
    """Load environment variables from .env file if ACCESS_TOKEN is not already set in environment."""
    if "ACCESS_TOKEN" in os.environ:
        return
    candidate_paths = [
        os.path.join(os.getcwd(), ".env"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")),
    ]
    for env_path in candidate_paths:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            clean_key = key.strip()
                            clean_val = value.strip().strip("'\"")
                            if clean_key and clean_val and clean_key not in os.environ:
                                os.environ[clean_key] = clean_val
            except Exception:
                pass
            break

def get_required_access_token() -> str:
    """Return the configured access token or default token."""
    load_env_vars()
    token = os.getenv("ACCESS_TOKEN")
    if token is not None:
        return token.strip()
    return DEFAULT_ACCESS_TOKEN

def verify_token(user_input: str) -> bool:
    """Verify if the user provided token matches the required access token."""
    required_token = get_required_access_token()
    if not required_token:
        return True
    return bool(user_input and user_input.strip() == required_token)
