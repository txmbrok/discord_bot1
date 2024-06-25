import logging
import logging.handlers
import os

def setup_discord_logger():
    """Setup logger for specific system activities within discord."""
    log_directory = 'logs'
    log_file = 'discord_system.log'

    # Check if the logs directory exists, if not create it
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    logger = logging.getLogger('discord.system')
    
    # Debug: Check how many times this setup is called
    print("Setting up discord.system logger")
    
    # Avoid adding multiple handlers if the logger is already configured
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_directory, log_file),  # Construct file path
            maxBytes=1024*1024*5,  # 5 MB
            backupCount=5,
            encoding='utf-8',
            mode='a'
        )
        formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    else:
        print("Logger already configured with handlers:", len(logger.handlers))

    return logger
