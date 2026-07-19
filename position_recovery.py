import json
import os


class PositionRecovery:

    FILE_NAME = "open_positions.json"

    # --------------------------------------------------

    def save(self, positions):
        """
        Saves the current open positions to a JSON file, stripping out
        the 'brain_decision' key from the decision data to prevent
        bloating or serialization issues.
        """
        try:
            safe_positions = {}

            for key, position in positions.items():
                safe_position = dict(position)

                if "decision" in safe_position:
                    decision = dict(safe_position["decision"])
                    decision.pop("brain_decision", None)
                    safe_position["decision"] = decision

                safe_positions[key] = safe_position

            with open(
                self.FILE_NAME,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    safe_positions,
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