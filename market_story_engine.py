class MarketStoryEngine:
    """
    ==========================================================
    Market Story Engine
    ==========================================================

    Mission
    -------
    Identify the dominant market narrative for the current
    trading session.

    A Market Story explains WHY capital is flowing into or
    out of sectors, industries and themes.

    Responsibilities
    ----------------
    1. Detect today's dominant market story
    2. Identify affected sectors
    3. Identify affected industries
    4. Identify affected themes
    5. Estimate confidence of the story
    6. Publish the story into BrainContext

    This engine NEVER:
    - Selects stocks
    - Generates BUY/SELL decisions
    - Executes trades
    - Calculates position size
    - Overrides execution strategy

    Inputs
    ------
    BrainContext

    Future Information Sources
    --------------------------
    - News Engine
    - Government Engine
    - Results Engine
    - Global Events
    - RBI / SEBI
    - Market Breadth
    - Sector Rotation
    - Theme Rotation

    Output
    ------
    context.market_story

    Author : H&M ORB AUTO TRADER
    ==========================================================
    """

    def __init__(self):
        pass

    def evaluate(self, context):
        """
        Determine today's dominant market story.

        Input
        -----
        BrainContext

        Updates
        -------
        context.market_story

        Returns
        -------
        context.market_story
        """
        pass