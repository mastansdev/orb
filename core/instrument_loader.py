from core.master_loader import master_loader


class InstrumentLoader:
    """
    Thin wrapper over MasterLoader.

    Keeps the existing interface so the rest of the
    project continues to work without modification.
    """

    # --------------------------------------------------

    def get_symbol(self, security_id):

        return master_loader.get_symbol(security_id)

    # --------------------------------------------------

    def get_security_id(self, symbol):

        return master_loader.get_security_id(symbol)

    # --------------------------------------------------

    def get_company_name(self, symbol):

        return master_loader.get_company_name(symbol)

    # --------------------------------------------------

    def get_sector(self, symbol):

        return master_loader.get_sector(symbol)

    # --------------------------------------------------

    def get_industry(self, symbol):

        return master_loader.get_industry(symbol)

    # --------------------------------------------------

    def get_themes(self, symbol):

        return master_loader.get_themes(symbol)

    # --------------------------------------------------

    def is_fno(self, symbol):

        return master_loader.is_fno(symbol)

    # --------------------------------------------------

    def get_lot_size(self, symbol):

        return master_loader.get_lot_size(symbol)

    # --------------------------------------------------

    def get_all_symbols(self):

        return master_loader.get_all_symbols()

    # --------------------------------------------------

    def get_all_security_ids(self):

        return master_loader.get_all_security_ids()