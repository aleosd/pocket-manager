from pathlib import Path


USER_HOME = Path.home()


APP_DATA_DIR_NAME = '.pocket-manager'
APP_DATA_DIR = USER_HOME.joinpath(APP_DATA_DIR_NAME)
DATABASE_FILE = 'pocket.sqlite'
DATABASE_PATH = APP_DATA_DIR.joinpath(DATABASE_FILE)

STATE_FILE = APP_DATA_DIR.joinpath('state')
CONFIG_PATH = APP_DATA_DIR.joinpath('config.json')

ARTICLES_GET_URL = 'https://getpocket.com/v3/get'
ARTICLES_CHANGE_URL = 'https://getpocket.com/v3/send'
