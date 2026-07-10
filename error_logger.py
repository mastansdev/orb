import os
import sys
import traceback
from datetime import datetime


class ErrorLogger:

    def __init__(self, log_folder="logs"):

        self.log_folder = log_folder

        os.makedirs(self.log_folder, exist_ok=True)

    # ---------------------------------------------------------

    def log(self, error):

        timestamp = datetime.now()

        file_name = os.path.join(
            self.log_folder,
            f"error_{timestamp.strftime('%Y%m%d_%H%M%S')}.log"
        )

        exc_type, exc_value, exc_tb = sys.exc_info()

        module = "Unknown"
        function = "Unknown"
        line = "Unknown"

        if exc_tb:

            last_frame = traceback.extract_tb(exc_tb)[-1]

            module = last_frame.filename
            function = last_frame.name
            line = last_frame.lineno

        with open(file_name, "w", encoding="utf-8") as file:

            file.write("=" * 80 + "\n")
            file.write("              ORB AUTO TRADER - ERROR REPORT\n")
            file.write("=" * 80 + "\n\n")

            file.write(f"Timestamp      : {timestamp}\n")
            file.write(f"Exception Type : {type(error).__name__}\n")
            file.write(f"Exception      : {str(error)}\n\n")

            file.write("Location\n")
            file.write("-" * 80 + "\n")
            file.write(f"Module         : {module}\n")
            file.write(f"Function       : {function}\n")
            file.write(f"Line Number    : {line}\n\n")

            file.write("Full Traceback\n")
            file.write("-" * 80 + "\n")
            file.write(traceback.format_exc())

            file.write("\n")
            file.write("=" * 80 + "\n")

        print("\n" + "=" * 80)
        print("ERROR OCCURRED")
        print("=" * 80)
        print(f"Exception : {type(error).__name__}")
        print(f"Message   : {error}")
        print(f"Module    : {module}")
        print(f"Function  : {function}")
        print(f"Line      : {line}")
        print(f"Log File  : {file_name}")
        print("=" * 80 + "\n")