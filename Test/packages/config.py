import inspect
import tkinter
from tkinter.filedialog import askopenfilename
import configparser
import re
from loguru import logger

def assign_config(config, section, val):
    """
    Get the user-configured section from the config.ini, puts it in a
    dictionary and returns it as the value "val"

    Parameter:
        config      [configparser]  -   configparser config object 
                                        from config.ini
        section     [string]        -   name of the section where the data for
                                        the dictionary is to be taken from
        val         [dictionary]    -   name of the dictionary that is to be
                                        returned
    """

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
        except ValueError:
            logger.error(f"Wrong value in config for => {key} : {value}")

    return val

def create_config(path: str):
    """
    Create a empty config and ask user for input to fill values

    Parameter:
        path            [str]       -       Path to the config file
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