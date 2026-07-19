class TickCache:

    def __init__(self):
        self.ticks = {}

    def update(self, security_id, ltp, ltt):

        self.ticks[security_id] = {
            "security_id": security_id,
            "ltp": ltp,
            "ltt": ltt
        }

    def get(self, security_id):

        return self.ticks.get(security_id)

    def get_all(self):

        return self.ticks

    def has_data(self):

        return len(self.ticks) > 0