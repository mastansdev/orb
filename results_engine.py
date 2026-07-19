from typing import Dict, Any, Optional
from master_loader import master_loader


class ResultsEngine:
    def __init__(self):
        # Type hint for tracking the internal data structure
        self.results: Dict[str, Dict[str, Any]] = {}
        self._initialize()

    # --------------------------------------------------

    def _get_default_data(self) -> Dict[str, Any]:
        """Returns a fresh dictionary of default values."""
        return {
            "status": "UNKNOWN",
            "score": 0,
            "revenue_surprise": 0.0,
            "profit_surprise": 0.0,
            "ebitda_surprise": 0.0,
            "guidance": "UNKNOWN",
            "result_date": None,
            "last_update": None
        }

    def _initialize(self) -> None:
        # Standardize symbols on initial load to match future cleanups
        for raw_symbol in master_loader.get_all_symbols():
            symbol = str(raw_symbol).strip().upper()
            self.results[symbol] = self._get_default_data()

        print("\n========================================")
        print("RESULTS ENGINE INITIALIZED")
        print("========================================")
        print(f"Stocks Loaded : {len(self.results)}")
        print("========================================")

    # --------------------------------------------------

    def update(self, symbol: str, **kwargs) -> None:
        """
        Dynamically updates the values for a given symbol.
        Ignores None values and keys that aren't part of the data model.
        """
        symbol = str(symbol).strip().upper()

        if symbol not in self.results:
            return

        target_data = self.results[symbol]
        
        for key, value in kwargs.items():
            if value is not None and key in target_data:
                target_data[key] = value

    # --------------------------------------------------

    def get_snapshot(self, symbol: str) -> Dict[str, Any]:
        symbol = str(symbol).strip().upper()

        if symbol not in self.results:
            return {
                "results": None
            }

        return {
            "results": self.results[symbol]
        }

    # --------------------------------------------------

    def get_results(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Returns the raw dictionary of results for a symbol."""
        symbol = str(symbol).strip().upper()
        return self.results.get(symbol)

    # --------------------------------------------------

    def reset(self) -> None:
        """Resets all stored symbols back to their default state."""
        for symbol in self.results:
            self.results[symbol] = self._get_default_data()