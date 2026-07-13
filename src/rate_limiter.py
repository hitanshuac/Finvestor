import json
import logging
import os
import re
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

LOCK_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".rate_limit_lock.json")


class RateLimitLockoutError(Exception):
    """Exception raised when the API is locally locked out due to previous rate limits."""

    def __init__(self, message: str, unlock_time: float):
        super().__init__(message)
        self.unlock_time = unlock_time


def _parse_duration(error_message: str) -> float:
    """
    Parse the Groq error message to extract the cooldown time in seconds.
    Example: "Please try again in 9m4.32s" -> 544.32 seconds.
    Example: "Please try again in 23h10m" -> 83400.0 seconds.
    """
    match = re.search(r"try again in (?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?", error_message)
    if not match:
        # Fallback to a default 10-minute timeout if we can't parse it
        return 600.0

    hours = float(match.group(1)) if match.group(1) else 0.0
    minutes = float(match.group(2)) if match.group(2) else 0.0
    seconds = float(match.group(3)) if match.group(3) else 0.0

    return (hours * 3600) + (minutes * 60) + seconds


def is_locked_out() -> bool:
    """Check if the system is currently locked out."""
    if not os.path.exists(LOCK_FILE):
        return False

    try:
        with open(LOCK_FILE) as f:
            data = json.load(f)

        unlock_time = data.get("unlock_timestamp", 0)
        current_time = time.time()

        if current_time < unlock_time:
            return True

        # Lockout has expired, clean up the file
        try:
            os.remove(LOCK_FILE)
        except OSError:
            pass
        return False
    except Exception as e:
        logger.error(f"Error checking rate limit lock file: {e}")
        return False


def get_lockout_info() -> tuple[bool, str]:
    """Get detailed lockout info (is_locked, human_readable_time_remaining)."""
    if not is_locked_out():
        return False, ""

    try:
        with open(LOCK_FILE) as f:
            data = json.load(f)
        unlock_time = data.get("unlock_timestamp", 0)
        remaining = unlock_time - time.time()
        if remaining <= 0:
            return False, ""

        td = timedelta(seconds=int(remaining))
        return True, str(td)
    except Exception:
        return False, ""


def set_lockout(error_message: str) -> None:
    """Set a global lockout by parsing the cooldown time from the error message."""
    # Prevent overwriting an existing, longer lockout
    if is_locked_out():
        return

    duration = _parse_duration(error_message)
    unlock_timestamp = time.time() + duration

    try:
        with open(LOCK_FILE, "w") as f:
            json.dump(
                {
                    "unlock_timestamp": unlock_timestamp,
                    "reason": error_message,
                    "created_at": datetime.utcnow().isoformat(),
                },
                f,
                indent=2,
            )
        logger.warning(f"API Rate Limit hit. System locked out for {duration} seconds.")
    except Exception as e:
        logger.error(f"Failed to write rate limit lock file: {e}")
