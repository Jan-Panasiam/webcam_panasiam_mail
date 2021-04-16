import inspect
import tkinter
from tkinter.filedialog import askopenfilename
import configparser
import re
from loguru import logger

def assign_config(config, section, val):
    
    val = {}

    if not section in config.keys():
        logger.error(f"No {section} in config => {config.keys()}")
        return None
    for key, value in config[section].items():
        x = re.search("^example-", key)
        if x:
            logger.warning("Fill your paths for the programm into "
                           f"[{section}]")
            return None
        try:
            val[key] = value
        except ValueError as err:
            logger.error(f"Wrong value in config for => {key} : {value}")

    return val


def create_config(path: str):
    """
        Parameter:
            path            [str]       -       Path to the config file

        Create a empty config and ask user for input to fill values
    """

    config = configparser.ConfigParser()
    config['PATH'] = {
            'example-path' : 'example/string'
    }
    config['EMAIL'] = {
        'example-email':'example-string'
    }


    with open(path, 'w') as configfile:
        config.write(configfile)

    logger.info("Fill out the Path and Email field of the config")

    return config