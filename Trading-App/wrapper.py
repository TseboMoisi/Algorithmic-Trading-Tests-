from ibapi.wrapper import EWrapper

# Receives requests from the IB API
class IBWrapper(EWrapper):
    def __init__(self):
        EWrapper.__init__(self)
        
        self.historical_data = {}

    def historicalData(self, request_id, bar):
        bar_data = (
            bar.date,
            bar.open,
            bar.high,
            bar.low,
            bar.close,
            bar.volume,
        )
        if request_id not in self.historical_data.keys():
            self.historical_data[request_id] = []
        self.historical_data[request_id].append(bar_data)