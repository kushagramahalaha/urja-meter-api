import os

from dotenv import load_dotenv

# Load configuration from the local .env file.
load_dotenv()

PORTAL_BASE_URL = os.getenv(
    "PORTAL_BASE_URL",
    "https://urja-ops.flockenergy.tech",
).rstrip("/")

PORTAL_EMAIL = os.getenv("PORTAL_EMAIL", "").strip()
PORTAL_PASSWORD = os.getenv("PORTAL_PASSWORD", "")

REQUEST_TIMEOUT_SECONDS = float(
    os.getenv("REQUEST_TIMEOUT_SECONDS", "15")
)


def validate_portal_config() -> None:
    """Ensure required portal credentials are configured."""
    if not PORTAL_EMAIL or not PORTAL_PASSWORD:
        raise ValueError(
            "Set PORTAL_EMAIL and PORTAL_PASSWORD in your local .env file."
        )