from enum import Enum

class SourceType(str, Enum):
    TRUSTED = "trusted"
    GENERAL = "general"

TRUSTED_DOMAINS = {
    "byjus.com",
    "vedantu.com",
    "khanacademy.org",
}
