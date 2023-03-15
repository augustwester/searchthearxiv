import os
import json

def setup_kaggle():
    KAGGLE_CONFIG_DIR = os.path.join(os.path.expandvars("$HOME"), ".kaggle")
    KAGGLE_CONFIG_FILE = os.path.join(KAGGLE_CONFIG_DIR, "kaggle.json")
    
    if os.path.exists(KAGGLE_CONFIG_FILE):
        print("✅ Kaggle already configured")
        return
    
    username = os.environ["KAGGLE_USERNAME"]
    api_key = os.environ["KAGGLE_API_KEY"]
    api_dict = {"username": username, "key": api_key}
    
    os.makedirs(KAGGLE_CONFIG_DIR, exist_ok=True)
    with open(KAGGLE_CONFIG_FILE, "w") as f:
        json.dump(api_dict, f)
    os.chmod(KAGGLE_CONFIG_FILE, 600)
        
    print("✅ Kaggle was successfully configured")
        
setup_kaggle()