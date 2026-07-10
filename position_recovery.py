import json
import os


class PositionRecovery:

    FILE_NAME = "open_positions.json"

    # --------------------------------------------------

    def save(self, positions):

        try:

            with open(
                self.FILE_NAME,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    positions,
                    file,
                    indent=4
                )

        except Exception as e:

            print(f"Position Recovery Save Error : {e}")

    # --------------------------------------------------

    def load(self):

        if not os.path.exists(self.FILE_NAME):
            return {}

        try:

            with open(
                self.FILE_NAME,
                "r",
                encoding="utf-8"
            ) as file:

                return json.load(file)

        except (json.JSONDecodeError, OSError) as e:

            print(f"Position Recovery Load Error : {e}")

            return {}

    # --------------------------------------------------

    def clear(self):

        try:

            if os.path.exists(self.FILE_NAME):
                os.remove(self.FILE_NAME)

        except Exception as e:

            print(f"Position Recovery Clear Error : {e}")

    # --------------------------------------------------

    def exists(self):

        return os.path.exists(self.FILE_NAME)