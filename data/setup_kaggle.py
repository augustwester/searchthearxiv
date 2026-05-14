import json
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def setup_kaggle() -> None:
    kaggle_config_dir = os.path.join(os.path.expandvars("$HOME"), ".kaggle")
    kaggle_config_file = os.path.join(kaggle_config_dir, "kaggle.json")

    if os.path.exists(kaggle_config_file):
        logger.info("Kaggle already configured")
        return

    username = os.environ["KAGGLE_USERNAME"]
    api_key = os.environ["KAGGLE_API_KEY"]
    api_dict = {"username": username, "key": api_key}

    os.makedirs(kaggle_config_dir, exist_ok=True)
    with open(kaggle_config_file, "w") as f:
        json.dump(api_dict, f)
    os.chmod(kaggle_config_file, 0o600)

    logger.info("Kaggle was successfully configured")


setup_kaggle()
