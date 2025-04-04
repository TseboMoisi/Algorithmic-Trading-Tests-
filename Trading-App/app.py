import threading
import time
from wrapper import IBWrapper
from client import IBClient
from contract import stock, future, option
from order import limit, BUY

class IBApp(IBWrapper, IBClient):
    def __init__(self, ip, port, client_id):

        IBWrapper.__init__(self)
        IBClient.__init__(self, wrapper=self)

        # Store connection parameters
        self.ip = ip
        self.port = port
        self.client_id = client_id

        # Connect and start thread
        self.connect(ip, port, client_id)
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        time.sleep(2)
if __name__ == "__main__":
    app = IBApp("127.0.0.1", 7497, client_id=10)
    # Import for contract functions
    aapl = stock("AAPL", "SMART", "USD")
    gbl = future("GBL", "EUREX", "202403")
    pltr = option("PLTR", "BOX", "20240315", 20, "C")
    limit_order = limit(BUY, 100, 190.00)
    time.sleep(30)
    app.disconnect()
