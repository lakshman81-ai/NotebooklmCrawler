import logging
import os
import sys

def setup_logging():
    """
    Configures the logging for the application.
    RULE: Each pipeline stage MUST log: start, success, failure (with exception).
    No stage may fail silently.
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        filename=os.path.join(log_dir, "app.log"),
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    # Add console handler to root logger
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)
