class OpenPositionManager:

    def __init__(self):

        self.positions = {}

    def add(self, security_id, trade):

        self.positions[security_id] = trade

    def remove(self, security_id):

        if security_id in self.positions:
            del self.positions[security_id]

    def get(self, security_id):

        return self.positions.get(security_id)

    def all(self):

        return self.positions

    def count(self):

        return len(self.positions)