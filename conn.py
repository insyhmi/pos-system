import os
import json
from dotenv import load_dotenv, dotenv_values

try:
    with open('config.json', 'r') as config_file:
        CONFIG = json.load(config_file)
except:
    print("Unable to open configuration file 'config.json'")

# USER CONNECTION TO DATABASE
load_dotenv()

r_host = os.getenv("R_HOST", default=CONFIG['db_host'])
r_username = os.getenv("R_USERNAME", default=CONFIG['db_username'])
r_password = os.getenv("R_PASSWORD", default=CONFIG['db_password'])
r_database = os.getenv("R_DATABASE", default=CONFIG['db_database'])
