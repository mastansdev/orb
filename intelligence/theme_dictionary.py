class ThemeDictionary:
    """
    Canonical Theme Dictionary

    Responsibility:
        • Standardize theme names
        • Remove synonyms
        • Normalize spelling
        • Normalize abbreviations

    This class NEVER:
        • ranks themes
        • scores conviction
        • reads market data
        • updates themes
    """

    def __init__(self):

        self._dictionary = {}

    # --------------------------------------------------

    def register(
        self,
        canonical,
        *aliases
    ):

        canonical = canonical.strip()

        self._dictionary[
            canonical.lower()
        ] = canonical

        for alias in aliases:

            if alias:

                self._dictionary[
                    alias.strip().lower()
                ] = canonical

    # --------------------------------------------------

    def normalize(
        self,
        theme
    ):

        if not theme:
            return None

        return self._dictionary.get(
            theme.strip().lower(),
            theme.strip()
        )

    # --------------------------------------------------

    def exists(
        self,
        theme
    ):

        if not theme:
            return False

        return (
            theme.strip().lower()
            in self._dictionary
        )

    # --------------------------------------------------

    def size(self):

        return len(self._dictionary)