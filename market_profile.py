from master_loader import master_loader


class MarketProfile:

    def __init__(self):

        self.profile = {}

        for symbol in master_loader.get_all_symbols():

            self.profile[symbol] = {

                "previous_close": None,

                "open": None,

                "gap_percent": 0.0,

                "loaded": False,

            }


market_profile = MarketProfile()