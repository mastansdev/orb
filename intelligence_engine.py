from datetime import datetime

# --------------------------------------------------
# Symbol Intelligence Providers
# --------------------------------------------------
SYMBOL_PROVIDERS = (
    "price",
    "sector",
    "industry",
    "theme",
    "relative_strength",
    "results",
)

# --------------------------------------------------
# Market Intelligence Providers
# --------------------------------------------------
MARKET_PROVIDERS = (
    "market_mood",
    "market_environment",
    "market_catalyst",
    "market_memory",
)


class IntelligenceEngine:

    def __init__(self, registry):
        self.registry = registry

    # --------------------------------------------------

    def get(self, symbol):
        snapshot = {
            "version": 1,
            "generated_at": datetime.now(),
            "symbol": {},
            "market": {},
            "health": {},
        }

        # ---------------------------------
        # Symbol Intelligence
        # ---------------------------------
        for provider in SYMBOL_PROVIDERS:
            engine = self.registry.get(provider)
            snapshot["health"][provider] = engine is not None

            if engine is None:
                continue

            try:
                snapshot["symbol"].update(
                    engine.get_snapshot(symbol)
                )
            except Exception:
                snapshot["health"][provider] = False

        # ---------------------------------
        # Market Intelligence
        # ---------------------------------
        for provider in MARKET_PROVIDERS:
            engine = self.registry.get(provider)
            snapshot["health"][provider] = engine is not None

            if engine is None:
                continue

            try:
                snapshot["market"].update(
                    engine.get_snapshot()
                )
            except TypeError:
                snapshot["market"].update(
                    engine.get_snapshot(symbol)
                )
            except Exception:
                snapshot["health"][provider] = False

        # ---------------------------------
        # Defaults
        # ---------------------------------
        symbol_snapshot = snapshot["symbol"]
        symbol_snapshot.setdefault("theme", [])
        symbol_snapshot.setdefault("relative_strength", None)
        symbol_snapshot.setdefault("results", None)

        market_snapshot = snapshot["market"]
        market_snapshot.setdefault("market_mood", None)
        market_snapshot.setdefault("market_environment", None)
        market_snapshot.setdefault("market_catalyst", None)
        market_snapshot.setdefault("market_memory", None)
        market_snapshot.setdefault("breadth", None)
        market_snapshot.setdefault("institutional_score", None)

        return snapshot

    # --------------------------------------------------

    def health(self):
        return {
            "registry": self.registry is not None,
            "symbol_providers": len(SYMBOL_PROVIDERS),
            "market_providers": len(MARKET_PROVIDERS),
            "total_providers": (
                len(SYMBOL_PROVIDERS)
                + len(MARKET_PROVIDERS)
            ),
        }

    # --------------------------------------------------

    def snapshot(self, symbol):
        return self.get(symbol)