class PaperExecution:

    def buy(self, security_id, symbol, price, qty):

        print("\n===================================")
        print(" PAPER BUY ORDER ")
        print("===================================")
        print(f"Symbol      : {symbol}")
        print(f"Security ID : {security_id}")
        print(f"Entry Price : {price}")
        print(f"Quantity    : {qty}")
        print("===================================\n")

    def sell(self, security_id, symbol, price, qty):

        print("\n===================================")
        print(" PAPER SELL ORDER ")
        print("===================================")
        print(f"Symbol      : {symbol}")
        print(f"Security ID : {security_id}")
        print(f"Exit Price  : {price}")
        print(f"Quantity    : {qty}")
        print("===================================\n")