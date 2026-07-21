class TickCache:

    def __init__(self):
        self.ticks = {}

    def update(self, security_id, ltp, ltt, volume=0):
        # volume (2026-07-21): defaulted to 0 so every existing
        # caller (tests, market_replay.py's CSV replay) that
        # doesn't pass it keeps working unchanged. Real volume
        # only starts flowing once the live feed subscribes in
        # Quote mode instead of Ticker -- see market_data.py.

        self.ticks[security_id] = {
            "security_id": security_id,
            "ltp": ltp,
            "ltt": ltt,
            "volume": volume,
        }

    def get(self, security_id):

        return self.ticks.get(security_id)

    def get_all(self):

        return self.ticks

    def has_data(self):

        return len(self.ticks) > 0