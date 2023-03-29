from web3 import Web3
import time
import requests
from requests.exceptions import HTTPError
import pandas as pd

class Web3Connection(object):
    RPC_URLS = dict()
    RPC_URLS['BSC'] = r"https://bsc-dataseed1.binance.org/"
    RPC_URLS['POLYGON'] = r"https://polygon-rpc.com/"
    RPC_URLS['AVALANCHE'] = r"https://api.avax.network/ext/bc/C/rpc"
    RPC_URLS['ETHEREUM'] = r"https://mainnet.infura.io/v3/9dbe8d08d93e4fb1bbf7d0ef5c4563e3"
    RPC_URLS['ARBITRUM'] = r"https://arb1.arbitrum.io/rpc"
    RPC_URLS['FANTOM'] = r"https://rpcapi.fantom.network/"
    #RPC_URLS['OPTIMISM'] = r"https://mainnet.optimism.io" #
    RPC_URLS['OPTIMISM'] = r"https://opt-mainnet.g.alchemy.com/v2/v7tHryP0DWkdsRqkKxZidV6gDEjIlK9R"
    RPC_URLS['MOONBEAM'] = r"https://1rpc.io/glmr"


    def __init__(self, chain, connection_attempts=5):
        url = self.RPC_URLS[chain]
        self.web3 = Web3(Web3.HTTPProvider(url))

        self.chain = chain

        while not self.web3.isConnected() and connection_attempts >= 0:
            time.sleep(1)
            self.web3 = Web3(Web3.HTTPProvider(url))
            connection_attempts -= 1

        if not self.web3.isConnected():
            raise ConnectionError

    def get_abi_from_address(self, address):
        chain_explorer = ChainExplorerWebsiteConnection(self.chain)

        return chain_explorer.get_abi_for_address(address)

class ChainExplorerWebsiteConnection(object):
    BASE_URLS = dict()
    BASE_URLS['BSC'] = r"https://api.bscscan.com/api?"
    BASE_URLS['POLYGON'] = r"https://api.polygonscan.com/api?"
    BASE_URLS['AVALANCHE'] = r"https://api.snowtrace.io/api?"
    BASE_URLS['ETHEREUM'] = r"https://api.etherscan.io/api?"
    BASE_URLS['ARBITRUM'] = r"https://api.arbiscan.io/api?"
    BASE_URLS['FANTOM'] = r"https://api.ftmscan.com/api?"
    BASE_URLS['OPTIMISM'] = r"https://api-optimistic.etherscan.io/api?"
    BASE_URLS['MOONBEAM'] = r"https://api-moonbeam.moonscan.io/api?"

    API_KEYS = dict()
    API_KEYS['BSC'] = "26C1N3PJDN1AMJ9XGZBHUGDH9YU45M5YXA"
    API_KEYS['POLYGON'] = r"7F1S8R4WM8NJEIA5PGD74B712UPY63FHB1"
    API_KEYS['AVALANCHE'] = r"TFVHCQKMFBAXKGYJ62Z4TBJEVY2MA2RNP4"
    API_KEYS['ETHEREUM'] = r"KWUTJI3X5GWXHYI162P8PQ48NS25242GCN"
    API_KEYS['ARBITRUM'] = r"MQWC8YFRAHEPUF7WEQD2AR4D6FTF74RXCR"
    API_KEYS['FANTOM'] = r"SUS8CSCW3RXQUGJ78FMG9RYGHXFM428WNY"
    API_KEYS['OPTIMISM'] = r"NUHBAGYFZYABSQ7S9G2KA9R477G5XYSYGT"
    API_KEYS['MOONBEAM'] = r"4P12TS177I3UB4FTJY2K5XB483417KFKYJ"

    def __init__(self, chain):
        #self.base_url = self.BASE_URLS[chain]
        #self.api_key = self.API_KEYS[chain]
        self.chain = chain

    def get_abi_for_address(self, contract_address):
        api_url = f"""{self.BASE_URLS[self.chain]}module=contract&action=getabi&address={contract_address}&apikey={self.API_KEYS[self.chain]}"""

        response = requests.get(api_url)

        if response.raise_for_status():
            print("build re-tries in UsefulFuncs")
            raise HTTPError

        response = response.json()
        if response['status']:
            abi = response['result']

            return abi

    def get_token_transfer_events(self, wallet_address):
        api_url = f"{self.BASE_URLS[self.chain]}module=account&action=tokentx&address={wallet_address}&startblock=0&endblock=999999999&sort=asc&apikey={self.API_KEYS[self.chain]}"

        response = requests.get(api_url)

        if response.raise_for_status():
            print("build re-tries in UsefulFuncs")
            raise HTTPError

        response = response.json()
        if response['status']:
            df = pd.DataFrame(response['result'])

            return df


