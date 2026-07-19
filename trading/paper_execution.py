from trading.execution_quality import ExecutionQuality


class PaperExecution:

    def __init__(self):
        self.execution_quality = ExecutionQuality()

    def buy(self, security_id, symbol, price, qty, segment=None):

        self.execution_quality.record(
            mode="PAPER",
            side="BUY",
            symbol=symbol,
            qty=qty,
            intended_price=price,
            fill_price=price,   # paper fills at intent
            order_id=f"PAPER_{symbol}",
            status="FILLED",
        )

        print("\n===================================")
        print(" PAPER BUY ORDER ")
        print("===================================")
        print(f"Symbol      : {symbol}")
        print(f"Security ID : {security_id}")
        print(f"Segment     : {segment or 'NSE_EQ'}")
        print(f"Entry Price : {price}")
        print(f"Quantity    : {qty}")
        print("===================================\n")

        return {
        "success": True,
        "order_id": f"PAPER_{symbol}",
        "message": "Paper order executed successfully."
    }

    def sell(self, security_id, symbol, price, qty, segment=None):

        self.execution_quality.record(
            mode="PAPER",
            side="SELL",
            symbol=symbol,
            qty=qty,
            intended_price=price,
            fill_price=price,
            order_id=f"PAPER_{symbol}",
            status="FILLED",
        )

        print("\n===================================")
        print(" PAPER SELL ORDER ")
        print("===================================")
        print(f"Symbol      : {symbol}")
        print(f"Security ID : {security_id}")
        print(f"Segment     : {segment or 'NSE_EQ'}")
        print(f"Exit Price  : {price}")
        print(f"Quantity    : {qty}")
        print("===================================\n")

        return {
        "success": True,
        "order_id": f"PAPER_{symbol}",
        "message": "Paper order executed successfully."
    }
