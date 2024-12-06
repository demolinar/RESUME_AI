import logging
import os
from datetime import datetime

def configure_logger(app):
    current_datetime = datetime.now().strftime("%Y-%m-%d %H")
    str_current_datetime = str(current_datetime).replace('-', '_').replace(' ', '__')

    log_folder = app.config['LOG_FOLDER']
    os.makedirs(log_folder, exist_ok=True)

    logger = logging.getLogger('PDFProcessor')
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(os.path.join(log_folder, f'app_{str_current_datetime}.log'))
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
