from core.master_loader import master_loader


def get_instruments():
    """
    Returns all instruments to subscribe
    from the Master Database.
    """

    return master_loader.get_all_instruments()