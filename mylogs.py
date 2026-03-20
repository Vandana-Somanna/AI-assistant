# # import logging

# # logging.basicConfig(filename="app.log",
# #                     format='%(asctime)s %(levelname)s: %(message)s',
# #                     filemode='w')
  
# # logger = logging.getLogger()
# # logger.setLevel(logging.DEBUG)
# # logger.debug("Harmless debug message")
# # logger.info("Just an information")
# # logger.warning("Its a warning")
# # logger.error("Did you try to divide by zero?")
# # logger.critical("Internet is down")

# # for handler in logger.handlers:
# #     handler.flush()

# # logging.shutdown()
# # print("Log file saved to app.log")

# # server.py or main.py (top)
# # from __future__ import annotations
# # import logging, logging.config
# # from pathlib import Path

# # LOG_DIR = Path(r"C:\Users\VandanaS\Desktop\AI_assistant\data\app_logs")
# # LOG_DIR.mkdir(parents=True, exist_ok=True)
# # LOG_FILE = LOG_DIR / "app.log"

# # LOGGING = {
# #     "version": 1,
# #     "disable_existing_loggers": False,  # keep uvicorn/fastapi loggers
# #     "formatters": {
# #         "default": { "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s" },
# #         "access":  { "format": "%(asctime)s | %(levelname)s | %(name)s | %(client_addr)s - %(request_line)s | %(status_code)s" },
# #     },
# #     "handlers": {
# #         "file": {
# #             "class": "logging.handlers.RotatingFileHandler",
# #             "formatter": "default",
# #             "filename": str(LOG_FILE),
# #             "maxBytes": 5 * 1024 * 1024,  # 5 MB
# #             "backupCount": 5,             # keep 5 old files
# #             "encoding": "utf-8",
# #         },
# #         "access_file": {
# #             "class": "logging.handlers.RotatingFileHandler",
# #             "formatter": "access",
# #             "filename": str(LOG_FILE),
# #             "maxBytes": 5 * 1024 * 1024,
# #             "backupCount": 5,
# #             "encoding": "utf-8",
# #         },
# #         "console": {
# #             "class": "logging.StreamHandler",
# #             "formatter": "default",
# #         },
# #     },
# #     "loggers": {
# #         "uvicorn.error":  {"handlers": ["file", "console"],      "level": "INFO", "propagate": False},
# #         "uvicorn.access": {"handlers": ["access_file", "console"],"level": "INFO", "propagate": False},
# #         "fastapi":        {"handlers": ["file", "console"],      "level": "INFO", "propagate": False},
# #         "starlette":      {"handlers": ["file", "console"],      "level": "INFO", "propagate": False},
# #         # your modules (use logging.getLogger("rag") etc.)
# #         "app":            {"handlers": ["file", "console"],      "level": "INFO", "propagate": False},
# #         "rag":            {"handlers": ["file", "console"],      "level": "INFO", "propagate": False},
# #         "mytools":        {"handlers": ["file", "console"],      "level": "INFO", "propagate": False},
# #     },
# #     "root": { "handlers": ["file", "console"], "level": "INFO" }
# # }
# # logging.config.dictConfig(LOGGING)
# # logger = logging.getLogger("app")  # use this in server.py if you want

# import logging
# import sys
# from pathlib import Path

# def setup_logging():
#     # 1. SETUP ABSOLUTE PATHS
#     BASE_DIR = Path(__file__).resolve().parent
#     LOG_FILE = BASE_DIR / "C:\\Users\\VandanaS\\Desktop\\AI_assistant\\app.log"

#     # 2. CREATE FORMATTER
#     formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

#     # 3. CREATE HANDLERS
#     # File Handler
#     file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
#     file_handler.setFormatter(formatter)

#     # Console Handler
#     stream_handler = logging.StreamHandler(sys.stdout)
#     stream_handler.setFormatter(formatter)

#     # 4. CONFIGURE ROOT LOGGER
#     root_logger = logging.getLogger()
#     root_logger.setLevel(logging.INFO)
    
#     # Remove existing handlers to avoid duplicates during reloads
#     if root_logger.hasHandlers():
#         root_logger.handlers.clear()
        
#     root_logger.addHandler(file_handler)
#     root_logger.addHandler(stream_handler)

#     return LOG_FILE

import datetime
from pathlib import Path

# Get the absolute path to the directory where this file lives
BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "C:\\Users\\VandanaS\\Desktop\\AI_assistant\\app.log"

def log_message(category, message):
    """Manually appends a message to app.log with a timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{category}] {message}\n"
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)
        f.flush() # Force it to write to disk immediately