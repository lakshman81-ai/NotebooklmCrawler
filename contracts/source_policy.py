from enum import Enum
import os

class SourceType(str, Enum):
    TRUSTED = "trusted"
    GENERAL = "general"

def _load_trusted_domains():
    # Load trusted domains from environment variable
    env_domains = os.getenv("TRUSTED_DOMAINS", "")
    if env_domains:
        return {d.strip() for d in env_domains.split(",") if d.strip()}

    return {
        "byjus.com",
        "vedantu.com",
        "khanacademy.org",
    }

TRUSTED_DOMAINS = _load_trusted_domains()
