from error_logger import ErrorLogger

logger = ErrorLogger()

try:

    x = 10 / 0

except Exception as e:

    logger.log(e)

print("Error logged successfully.")