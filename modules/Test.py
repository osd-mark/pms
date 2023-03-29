import pandas as pd

from FetchPortfolio import *
from OsdWeb3 import *
import pandas as pd

osd_address = "0xd3ff664c4a2e505fca9ff9200f9191db3009c8a1"

ts = DebankPortfolioTimeSeries()

block_explorer = ChainExplorerWebsiteConnection('')

total_txs = pd.DataFrame()

for chain in block_explorer.BASE_URLS:
    txs = ChainExplorerWebsiteConnection(chain).get_token_transfer_events(osd_address)

    total_txs = pd.concat([total_txs, txs])

print("")