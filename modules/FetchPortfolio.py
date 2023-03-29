import datetime
import os

import numpy as np
import pandas as pd
import requests
import time
from pycoingecko import CoinGeckoAPI
from web3 import Web3
from modules.OneDriveInterface import DataSnapClass

def parse_debank_protocol_api_object(portfolio_positions, add_debank_id=False):
    portfolio_parsed_positions = list()
    portfolio_column_names = ['Chain', 'Dapp', 'Pool', 'Token', 'Position', 'Price', 'USD Value']

    if add_debank_id:
        portfolio_column_names += ['Debank ID']

    if isinstance(portfolio_positions, dict):
        portfolio_positions = [portfolio_positions]

    for platform_positions in portfolio_positions:
        chain = platform_positions['chain']
        dapp = platform_positions['name']

        if add_debank_id:
            debank_id = platform_positions['id']

        for platform_position in platform_positions['portfolio_item_list']:
            supply_token_list = platform_position['detail'].get('supply_token_list', [])
            reward_token_list = platform_position['detail'].get('reward_token_list', [])

            pool = []
            for supply_token in supply_token_list:
                pool.append(supply_token['symbol'].upper())

            pool = "/".join(sorted(pool))

            for supply_token in supply_token_list:
                token = supply_token['symbol'].upper()
                position = supply_token['amount']
                price = supply_token['price']
                usd_value = position * price
                ca = supply_token['id']

                if add_debank_id:
                    portfolio_parsed_positions.append([chain, dapp, pool, token, position, price, usd_value, debank_id])
                else:
                    portfolio_parsed_positions.append([chain, dapp, pool, token, position, price, usd_value])

            for reward_token in reward_token_list:
                token = reward_token['symbol']
                position = reward_token['amount']
                price = reward_token['price']
                usd_value = position * price
                ca = reward_token['id']

                if add_debank_id:
                    portfolio_parsed_positions.append([chain, dapp, pool, token, position, price, usd_value, debank_id])
                else:
                    portfolio_parsed_positions.append([chain, dapp, pool, token, position, price, usd_value])

    df = pd.DataFrame(portfolio_parsed_positions, columns=portfolio_column_names)

    return df

def parse_debank_tokens_api_object(portfolio_positions):
    portfolio_parsed_positions = list()
    portfolio_column_names = ['Chain', 'Dapp', 'Pool', 'Token', 'Position', 'Price', 'USD Value']

    for token_positions in portfolio_positions:
        if token_positions['is_core'] == True:
            chain = token_positions['chain']
            dapp = "Fireblocks Vault"
            pool = np.NAN
            position = token_positions['amount']
            price = token_positions['price']
            token = token_positions['symbol']
            usd_value = position * price

            portfolio_parsed_positions.append([chain, dapp, pool, token, position, price, usd_value])

    df = pd.DataFrame(portfolio_parsed_positions, columns=portfolio_column_names)

    return df

def parse_honey_positions(honey_snap): #grizzly_pool_honey, honey_price, pool_name):
    chain = "bsc"
    dapp = "GrizzlyFi"
    token = "GHNY"

    honey_position = list()

    for key in honey_snap:
        if key != 'GHNY Price':
            grizzly_pool_honey_usd = honey_snap[key] * honey_snap['GHNY Price']

            honey_position.append(
                [chain, dapp, key, token, honey_snap[key], honey_snap['GHNY Price'], grizzly_pool_honey_usd])

    column_names = ['Chain', 'Dapp', 'Pool', 'Token', 'Position', 'Price', 'USD Value']
    df = pd.DataFrame(honey_position, columns=column_names)

    return df

def get_defi_positions(address = "0xd3ff664c4a2e505fca9ff9200f9191db3009c8a1", add_debank_id=False):
    debank_base_url = "https://pro-openapi.debank.com"
    protocol_balances_endpoint = "/v1/user/all_complex_protocol_list?"

    osd_api_key = "2c06e512bcd288e6a32128331ea5a640752d2e34"
    headers = {'accept': 'application/json', 'AccessKey': osd_api_key}

    protocol_balances_url = f"{debank_base_url}{protocol_balances_endpoint}id={address}"
    api_call = requests.get(protocol_balances_url, headers=headers)

    while api_call.raise_for_status():
        time.sleep(60)

        api_call = requests.get(protocol_balances_url, headers=headers)
    portfolio_positions = api_call.json()

    df = parse_debank_protocol_api_object(portfolio_positions, add_debank_id)

    return df

def get_wallet_tokens():
    debank_base_url = "https://pro-openapi.debank.com"
    protocol_balances_endpoint = "/v1/user/all_token_list?"

    osd_api_key = "2c06e512bcd288e6a32128331ea5a640752d2e34"
    headers = {'accept': 'application/json', 'AccessKey': osd_api_key}

    osd_address = "0xd3ff664c4a2e505fca9ff9200f9191db3009c8a1"

    protocol_balances_url = f"{debank_base_url}{protocol_balances_endpoint}id={osd_address}"
    api_call = requests.get(protocol_balances_url, headers=headers)

    while api_call.raise_for_status():
        time.sleep(60)

        api_call = requests.get(protocol_balances_url, headers=headers)
    portfolio_positions = api_call.json()

    df = parse_debank_tokens_api_object(portfolio_positions)

    return df

def get_honey_positions():
    osd_address = "0xd3fF664C4A2e505FCa9Ff9200F9191dB3009c8a1"

    url = r"https://bsc-dataseed1.binance.org/"
    w3 = Web3(Web3.HTTPProvider(url))

    grizzly_usdc_usdt_address = "0x7E5762A7D68Fabcba39349229014c59Db6dc5eB0"
    grizzly_usdc_usdt_abi = """[{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":false,"internalType":"uint256","name":"lpAmount","type":"uint256"},{"indexed":true,"internalType":"enum IStableGrizzly.Strategy","name":"currentStrategy","type":"uint8"}],"name":"DepositEvent","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":false,"internalType":"uint256","name":"honeyAmount","type":"uint256"}],"name":"GrizzlyStrategyClaimHoneyEvent","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":false,"internalType":"uint256","name":"honeyAmount","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"bnbAmount","type":"uint256"}],"name":"GrizzlyStrategyClaimLpEvent","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint8","name":"version","type":"uint8"}],"name":"Initialized","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"account","type":"address"}],"name":"Paused","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"role","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"previousAdminRole","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"newAdminRole","type":"bytes32"}],"name":"RoleAdminChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"role","type":"bytes32"},{"indexed":true,"internalType":"address","name":"account","type":"address"},{"indexed":true,"internalType":"address","name":"sender","type":"address"}],"name":"RoleGranted","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"role","type":"bytes32"},{"indexed":true,"internalType":"address","name":"account","type":"address"},{"indexed":true,"internalType":"address","name":"sender","type":"address"}],"name":"RoleRevoked","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"caller","type":"address"},{"indexed":false,"internalType":"uint256","name":"bnbAmount","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"standardShare","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"grizzlyShare","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"stablecoinShare","type":"uint256"}],"name":"StakeRewardsEvent","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":false,"internalType":"uint256","name":"honeyAmount","type":"uint256"}],"name":"StandardStrategyClaimHoneyEvent","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":true,"internalType":"enum IStableGrizzly.Strategy","name":"fromStrategy","type":"uint8"},{"indexed":true,"internalType":"enum IStableGrizzly.Strategy","name":"toStrategy","type":"uint8"}],"name":"SwitchStrategyEvent","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"account","type":"address"}],"name":"Unpaused","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":false,"internalType":"uint256","name":"lpAmount","type":"uint256"},{"indexed":true,"internalType":"enum IStableGrizzly.Strategy","name":"currentStrategy","type":"uint8"}],"name":"WithdrawEvent","type":"event"},{"inputs":[],"name":"AveragePriceOracle","outputs":[{"internalType":"contract IAveragePriceOracle","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"DECIMAL_OFFSET","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"DEFAULT_ADMIN_ROLE","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"DEX","outputs":[{"internalType":"contract IDEX","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"DevTeam","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"FUNDS_RECOVERY_ROLE","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"HoneyBnbLpToken","outputs":[{"internalType":"contract IERC20Upgradeable","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"HoneyToken","outputs":[{"internalType":"contract IHoney","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"LPToken","outputs":[{"internalType":"contract IERC20Upgradeable","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"MAX_PERCENTAGE","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"PAUSER_ROLE","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"PoolID","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"Referral","outputs":[{"internalType":"contract IReferral","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"RewardToken","outputs":[{"internalType":"contract IERC20Upgradeable","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"StableSwap","outputs":[{"internalType":"contract IPancakeStableSwap","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"StakingContract","outputs":[{"internalType":"contract IMasterChef","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"StakingPool","outputs":[{"internalType":"contract IStakingPool","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"TokenA","outputs":[{"internalType":"contract IERC20Upgradeable","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"TokenB","outputs":[{"internalType":"contract IERC20Upgradeable","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"UPDATER_ROLE","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"ZAP_ROLE","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"beeEfficiencyLevel","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"enum IStableGrizzly.Strategy","name":"toStrategy","type":"uint8"},{"internalType":"address[]","name":"fromToken","type":"address[]"},{"internalType":"address[]","name":"toToken","type":"address[]"},{"internalType":"uint256[]","name":"amountIn","type":"uint256[]"},{"internalType":"uint256[]","name":"amountOut","type":"uint256[]"},{"internalType":"uint256","name":"slippage","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"changeStrategy","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address","name":"referralGiver","type":"address"},{"internalType":"address[]","name":"fromToken","type":"address[]"},{"internalType":"address[]","name":"toToken","type":"address[]"},{"internalType":"uint256[]","name":"amountIn","type":"uint256[]"},{"internalType":"uint256[]","name":"amountOut","type":"uint256[]"},{"internalType":"uint256","name":"slippage","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"depositLp","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"}],"name":"getGrizzlyStrategyBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"}],"name":"getGrizzlyStrategyLpRewards","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"participant","type":"address"}],"name":"getGrizzlyStrategyParticipantData","outputs":[{"components":[{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"honeyMask","type":"uint256"},{"internalType":"uint256","name":"pendingHoney","type":"uint256"},{"internalType":"uint256","name":"lpMask","type":"uint256"},{"internalType":"uint256","name":"pendingLp","type":"uint256"},{"internalType":"uint256","name":"pendingAdditionalHoney","type":"uint256"},{"internalType":"uint256","name":"additionalHoneyMask","type":"uint256"}],"internalType":"struct StableGrizzlyStrategy.GrizzlyStrategyParticipant","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"}],"name":"getGrizzlyStrategyStakedHoney","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"role","type":"bytes32"}],"name":"getRoleAdmin","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"}],"name":"getStablecoinStrategyBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"participant","type":"address"}],"name":"getStablecoinStrategyParticipantData","outputs":[{"components":[{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"rewardMask","type":"uint256"},{"internalType":"uint256","name":"totalReinvested","type":"uint256"}],"internalType":"struct StableStableCoinStrategy.StablecoinStrategyParticipant","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"}],"name":"getStandardStrategyBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"}],"name":"getStandardStrategyHoneyRewards","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"participant","type":"address"}],"name":"getStandardStrategyParticipantData","outputs":[{"components":[{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"lpMask","type":"uint256"},{"internalType":"uint256","name":"rewardMask","type":"uint256"},{"internalType":"uint256","name":"pendingRewards","type":"uint256"},{"internalType":"uint256","name":"totalReinvested","type":"uint256"}],"internalType":"struct StableStandardStrategy.StandardStrategyParticipant","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getUpdatedState","outputs":[{"internalType":"enum IStableGrizzly.Strategy","name":"currentStrategy","type":"uint8"},{"internalType":"uint256","name":"deposited","type":"uint256"},{"internalType":"uint256","name":"balance","type":"uint256"},{"internalType":"uint256","name":"totalReinvested","type":"uint256"},{"internalType":"uint256","name":"earnedHoney","type":"uint256"},{"internalType":"uint256","name":"earnedBnb","type":"uint256"},{"internalType":"uint256","name":"stakedHoney","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"role","type":"bytes32"},{"internalType":"address","name":"account","type":"address"}],"name":"grantRole","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"grizzlyStrategyClaimHoney","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"grizzlyStrategyClaimLP","outputs":[{"internalType":"uint256","name":"claimedHoney","type":"uint256"},{"internalType":"uint256","name":"claimedBnb","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"grizzlyStrategyDeposits","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"grizzlyStrategyLastAdditionalHoneyBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"grizzlyStrategyLastHoneyBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"grizzlyStrategyLastLpBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"role","type":"bytes32"},{"internalType":"address","name":"account","type":"address"}],"name":"hasRole","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_Admin","type":"address"},{"internalType":"address","name":"_StakingContractAddress","type":"address"},{"internalType":"address","name":"_StakingPoolAddress","type":"address"},{"internalType":"address","name":"_HoneyTokenAddress","type":"address"},{"internalType":"address","name":"_HoneyBnbLpTokenAddress","type":"address"},{"internalType":"address","name":"_DevTeamAddress","type":"address"},{"internalType":"address","name":"_ReferralAddress","type":"address"},{"internalType":"address","name":"_AveragePriceOracleAddress","type":"address"},{"internalType":"address","name":"_DEXAddress","type":"address"},{"internalType":"uint256","name":"_PoolID","type":"uint256"},{"internalType":"address","name":"_StableSwapAddress","type":"address"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"lastStakeRewardsCake","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"lastStakeRewardsCall","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"lastStakeRewardsDeposit","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"lastStakeRewardsDuration","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"lpRoundMask","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"pause","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"paused","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"role","type":"bytes32"},{"internalType":"address","name":"account","type":"address"}],"name":"renounceRole","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"restakeThreshold","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"role","type":"bytes32"},{"internalType":"address","name":"account","type":"address"}],"name":"revokeRole","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"stablecoinStrategyDeposits","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"standardStrategyClaimHoney","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"standardStrategyDeposits","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes4","name":"interfaceId","type":"bytes4"}],"name":"supportsInterface","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalHoneyRewards","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalRewardsClaimed","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalStablecoinBnbReinvested","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalStandardBnbReinvested","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalUnusedTokenA","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalUnusedTokenB","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"unpause","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_newBeeEfficiencyLevel","type":"uint256"}],"name":"updateBeeEfficiencyLevel","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_restakeThreshold","type":"uint256"}],"name":"updateRestakeThreshold","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"updateRoundMasks","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"userStrategy","outputs":[{"internalType":"enum IStableGrizzly.Strategy","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address[]","name":"fromToken","type":"address[]"},{"internalType":"address[]","name":"toToken","type":"address[]"},{"internalType":"uint256[]","name":"amountIn","type":"uint256[]"},{"internalType":"uint256[]","name":"amountOut","type":"uint256[]"},{"internalType":"uint256","name":"slippage","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"withdrawToLp","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]"""
    grizzly_usdc_usdt_contract = w3.eth.contract(address=grizzly_usdc_usdt_address, abi=grizzly_usdc_usdt_abi)

    grizzly_busd_usdc_address = "0xCCf6356C96Eadd2702fe6f5Ef99B1C0a3966EDf7"
    grizzly_busd_usdc_contract = w3.eth.contract(address=grizzly_busd_usdc_address, abi=grizzly_usdc_usdt_abi)

    one_token = w3.toWei(1, 'Ether')

    grizzly_usdc_usdt_honey = grizzly_usdc_usdt_contract.functions.getGrizzlyStrategyStakedHoney(
        osd_address).call() / one_token

    grizzly_busd_usdc_honey = grizzly_busd_usdc_contract.functions.getGrizzlyStrategyStakedHoney(
        osd_address).call() / one_token

    #cg = CoinGeckoAPI()

    header = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
    honey_price = requests.get("http://api.coingecko.com/api/v3/simple/price?ids=grizzly-honey&vs_currencies=usd",
                               headers=header)
    honey_price = honey_price.json()['grizzly-honey']['usd']

    grizzly_usdc_usdt_honey_usd = grizzly_usdc_usdt_honey * honey_price
    grizzly_busd_usdc_honey_usd = grizzly_busd_usdc_honey * honey_price

    portfolio_parsed_positions = list()
    portfolio_column_names = ['Chain', 'Dapp', 'Pool', 'Token', 'Position', 'Price', 'USD Value']

    chain = "bsc"
    dapp = "GrizzlyFi"
    token = "GHNY"

    pool = "USDC/USDT"

    portfolio_parsed_positions.append(
        [chain, dapp, pool, token, grizzly_usdc_usdt_honey, honey_price, grizzly_usdc_usdt_honey_usd])

    pool = "BUSD/USDC"

    portfolio_parsed_positions.append(
        [chain, dapp, pool, token, grizzly_busd_usdc_honey, honey_price, grizzly_busd_usdc_honey_usd])

    df = pd.DataFrame(portfolio_parsed_positions, columns=portfolio_column_names)

    return df

class DeBankPortfolio(object):
    AGGREGATION_LEVELS = ['Chain', 'Token', 'Dapp', 'Pool']

    def __init__(self, debank_snap=None, add_debank_id=False):
        if debank_snap is not None:
            #if isinstance(debank_snap, dict):
            self.defi_positions = parse_debank_protocol_api_object(debank_snap['protocol'])

            if 'token' in debank_snap:
                self.wallet_tokens = parse_debank_tokens_api_object(debank_snap['token'])
            else:
                self.wallet_tokens = pd.DataFrame()

            if 'Honey' in debank_snap:
                self.contract_call_positions = parse_honey_positions(debank_snap['Honey'])
            else:
                self.contract_call_positions = pd.DataFrame()
            '''else:
                self.defi_positions = parse_debank_protocol_api_object(debank_snap)
                self.wallet_tokens = pd.DataFrame()
                self.contract_call_positions = pd.DataFrame()'''

        else:
            self.defi_positions = get_defi_positions(add_debank_id=add_debank_id)
            self.wallet_tokens = get_wallet_tokens()
            self.contract_call_positions = get_honey_positions()

        self.portfolio = pd.concat([self.wallet_tokens, self.defi_positions, self.contract_call_positions])

    def get_portfolio_stablecoins(self):
        pools = self.defi_positions['Pool'].tolist()

        stables = [pool.split("/") for pool in pools if pool != 'QUICK']
        stables = [item.upper() for sublist in stables for item in sublist]

        stables = list(set(sorted(stables)))

        return stables

    def get_portfolio_dapps(self):
        return list(set(self.defi_positions['Dapp'].to_list()))

    def get_portfolio_debank_ids(self):
        defi_positions = get_defi_positions(add_debank_id=True)

        return list(set(defi_positions['Debank ID'].to_list()))

    def get_chain_weights(self):
        fund_assets = self.get_fund_assets()

        return fund_assets.groupby('Chain')['USD Value'].sum() / fund_assets['USD Value'].sum()

    def get_coin_weights(self):
        fund_assets = self.get_fund_assets()

        return fund_assets.groupby('Token')['USD Value'].sum() / fund_assets['USD Value'].sum()

    def get_dapp_weights(self):
        fund_assets = self.get_fund_assets()

        return fund_assets.groupby('Dapp')['USD Value'].sum() / fund_assets['USD Value'].sum()

    def get_pool_weights(self):
        fund_assets = self.get_fund_assets()

        fund_assets.loc[fund_assets['Dapp'] == 'Fireblocks Vault', 'Pool'] = 'Wallet'
        df = fund_assets.groupby(['Chain', 'Dapp', 'Pool'])['USD Value'].sum().reset_index()
        df['Weight'] = (df['USD Value'] / df['USD Value'].sum()) * 100

        return df

    def get_aggregated_weights(self, aggregation_level: str):
        if aggregation_level not in self.AGGREGATION_LEVELS:
            raise ValueError("Aggregation Level Not Valid")

        if aggregation_level == 'Chain':
            return self.get_chain_weights()
        elif aggregation_level == 'Token':
            return self.get_coin_weights()
        elif aggregation_level == 'Dapp':
            return self.get_dapp_weights()
        elif aggregation_level == 'Pool':
            return self.get_pool_weights()

    def get_fund_assets(self):
        return self.portfolio[~(self.portfolio['Token'].isin(['AVAX', 'BNB', 'ETH', 'MATIC', 'GLMR']))]

    def get_nav(self):
        fund_assets = self.get_fund_assets()

        return fund_assets['USD Value'].sum()

    def filter_small_balances(self, threshold=0.0001):
        self.portfolio['Weight'] = self.portfolio['USD Value'] / self.portfolio['USD Value'].sum()

        self.small_balances = self.portfolio[self.portfolio['Weight'] < threshold]

        self.portfolio = self.portfolio[self.portfolio['Weight'] >= threshold]

        self.portfolio.drop(columns='Weight', inplace=True)

    def sort_small_balances(self, threshold=0.0001):
        self.portfolio['Weight'] = self.portfolio['USD Value'] / self.portfolio['USD Value'].sum()

        self.small_balances = self.portfolio[self.portfolio['Weight'] < threshold]

        self.portfolio = self.portfolio[self.portfolio['Weight'] >= threshold]

        self.portfolio = pd.concat([self.portfolio, self.small_balances])

        self.portfolio.drop(columns='Weight', inplace=True)




r"""class DebankPortfolioTimeSeries(DeBankPortfolio):
    SNAPS_PATH = r"C:\Users\lyons\OneDrive - Old Street Digital\OSD Shared Drive\Data Snapping\CIF Snap/"
    MONTH_END_SNAPS_PATH = r"C:\Users\lyons\OneDrive - Old Street Digital\Investment Files\Data Snapping\Raw Snaps\CIF Month End/"

    def __init__(self, debank_snap_path=None, month_end=False, *__args):
        super().__init__(*__args)

        if month_end:
            debank_snap_path = self.MONTH_END_SNAPS_PATH
        elif debank_snap_path is None:
            debank_snap_path = self.SNAPS_PATH

        self.portfolio = pd.DataFrame()
        self.defi_positions = pd.DataFrame()
        self.wallet_tokens = pd.DataFrame()
        self.contract_call_positions = pd.DataFrame()

        for date in os.listdir(debank_snap_path):
            if date == '.DS_Store':
                continue
            if 'CIF' in debank_snap_path:
                file_name = 'CIF_debank.pkl'
            elif 'DeBank' in debank_snap_path:
                file_name = 'user_protocol.pkl'
            else:
                raise NotImplementedError("Please add pkl file name for this folder")

            full_path = os.path.join(debank_snap_path, date, file_name)

            pkl = pd.read_pickle(full_path)

            day_portfolio = DeBankPortfolio(pkl)

            #self.update_dfs(pkl, date)

            self.portfolio = self.update_df(self.portfolio, day_portfolio.portfolio, date)
            self.defi_positions = self.update_df(self.defi_positions, day_portfolio.defi_positions, date)
            self.wallet_tokens = self.update_df(self.wallet_tokens, day_portfolio.wallet_tokens, date)
            self.contract_call_positions = self.update_df(self.contract_call_positions, day_portfolio.contract_call_positions, date)

        #self.portfolio.sort_values(by='Date')
        #self.defi_positions.sort_values(by='Date')
        #self.wallet_tokens.sort_values(by='Date')
        #self.contract_call_positions.sort_values(by='Date')

    def update_df(self, time_series_df, day_df, date):
        day_df['Date'] = date

        day_df = day_df[['Date'] + [col for col in day_df.columns if col !='Date']]

        time_series_df = pd.concat([time_series_df, day_df])

        return time_series_df

    '''def update_dfs(self, day_pkl, date):
        
        if isinstance(day_pkl, dict):
            day_defi_positions = parse_debank_protocol_api_object(day_pkl['protocol'])
            day_wallet_tokens = parse_debank_tokens_api_object(day_pkl['token'])

            if 'Honey' in day_pkl:
                day_contract_call_positions = parse_honey_positions(day_pkl['Honey'])
            else:
                day_contract_call_positions = pd.DataFrame()
        else:
            day_defi_positions = parse_debank_protocol_api_object(day_pkl)
            day_wallet_tokens = pd.DataFrame()
            day_contract_call_positions = pd.DataFrame()

        self.defi_positions = self.update_df(self.defi_positions, day_defi_positions, date)
        self.wallet_tokens = self.update_df(self.wallet_tokens, day_wallet_tokens, date)
        self.contract_call_positions = self.update_df(self.contract_call_positions, day_contract_call_positions, date)

        day_portfolio = pd.concat([day_wallet_tokens, day_defi_positions, day_contract_call_positions])

        self.portfolio = self.update_df(self.portfolio, day_portfolio, date)'''

    def get_nav_series(self):
        fund_assets = self.get_fund_assets()

        navs = fund_assets.groupby(['Date'])['USD Value'].sum()

        navs.index = pd.DatetimeIndex(navs.index)

        navs[navs.index < pd.to_datetime("2023-03-01")] /= 200
        navs[navs.index >= pd.to_datetime("2023-03-01")] /= 782.6148

        idx = pd.date_range(navs.index[0], navs.index[-1], freq="D")
        navs = navs.reindex(idx)
        navs = navs.interpolate('linear')

        navs.name = 'NAV'
        navs.index.name = 'Date'

        return navs

    def get_return_series(self, rolling_window=1, annualised=False):
        navs = self.get_nav_series()

        returns = navs.pct_change()

        if annualised:
            '''returns = returns + 1
            returns = returns.pow(365) - 1'''

            returns = returns * 365

        returns = returns * 100

        returns = returns.rolling(window=rolling_window).mean()

        returns.name = 'Returns'
        returns.index.name = 'Date'

        return returns
"""

class DebankPortfolioTimeSeries(DeBankPortfolio):
    def __init__(self, month_end=False, *__args):
        super().__init__(*__args)

        fund_snaps = DataSnapClass('CIF').read_time_series_snaps()

        self.daily_portfolio_objects = dict()
        self.portfolio = pd.DataFrame()
        self.defi_positions = pd.DataFrame()
        self.wallet_tokens = pd.DataFrame()
        self.contract_call_positions = pd.DataFrame()

        for date in reversed(fund_snaps):
            day_portfolio = DeBankPortfolio(fund_snaps[date])

            self.daily_portfolio_objects[date] = day_portfolio
            self.portfolio = self.update_df(self.portfolio, day_portfolio.portfolio, date)
            self.defi_positions = self.update_df(self.defi_positions, day_portfolio.defi_positions, date)
            self.wallet_tokens = self.update_df(self.wallet_tokens, day_portfolio.wallet_tokens, date)
            self.contract_call_positions = self.update_df(self.contract_call_positions,
                                                          day_portfolio.contract_call_positions, date)

    def update_df(self, time_series_df, day_df, date):
        day_df['Date'] = date

        day_df = day_df[['Date'] + [col for col in day_df.columns if col != 'Date']]

        time_series_df = pd.concat([time_series_df, day_df])

        return time_series_df

    '''def update_dfs(self, day_pkl, date):

        if isinstance(day_pkl, dict):
            day_defi_positions = parse_debank_protocol_api_object(day_pkl['protocol'])
            day_wallet_tokens = parse_debank_tokens_api_object(day_pkl['token'])

            if 'Honey' in day_pkl:
                day_contract_call_positions = parse_honey_positions(day_pkl['Honey'])
            else:
                day_contract_call_positions = pd.DataFrame()
        else:
            day_defi_positions = parse_debank_protocol_api_object(day_pkl)
            day_wallet_tokens = pd.DataFrame()
            day_contract_call_positions = pd.DataFrame()

        self.defi_positions = self.update_df(self.defi_positions, day_defi_positions, date)
        self.wallet_tokens = self.update_df(self.wallet_tokens, day_wallet_tokens, date)
        self.contract_call_positions = self.update_df(self.contract_call_positions, day_contract_call_positions, date)

        day_portfolio = pd.concat([day_wallet_tokens, day_defi_positions, day_contract_call_positions])

        self.portfolio = self.update_df(self.portfolio, day_portfolio, date)'''

    def get_nav_series(self):
        fund_assets = self.get_fund_assets()

        navs = fund_assets.groupby(['Date'])['USD Value'].sum()

        navs.index = pd.DatetimeIndex(navs.index)

        navs[navs.index < pd.to_datetime("2023-03-01")] /= 200
        navs[navs.index >= pd.to_datetime("2023-03-01")] /= 782.6148

        idx = pd.date_range(navs.index[0], navs.index[-1], freq="D")
        navs = navs.reindex(idx)
        navs = navs.interpolate('linear')

        navs.name = 'NAV'
        navs.index.name = 'Date'

        return navs

    def get_return_series(self, rolling_window=1, annualised=False):
        navs = self.get_nav_series()

        returns = navs.pct_change()

        if annualised:
            '''returns = returns + 1
            returns = returns.pow(365) - 1'''

            returns = returns * 365

        returns = returns * 100

        returns = returns.rolling(window=rolling_window).mean()

        returns.name = 'Returns'
        returns.index.name = 'Date'

        return returns

class PortfolioTimeSeries(DebankPortfolioTimeSeries):
    CIRCLE_FILE_LOC = r"C:\Users\lyons\Downloads\transaction_history_20230322_095812.xlsx"
    SIGNATURE_FILE_LOC = r"C:\Users\lyons\Downloads\Export-22032023.csv"

    def __init__(self, circle_file_loc=None, signature_bank_file_loc=None, debank_snap_path=None, month_end=False, *__args):
        super().__init__(month_end=month_end, *__args)

        if circle_file_loc == None:
            circle_file_loc = self.CIRCLE_FILE_LOC
        if signature_bank_file_loc == None:
            signature_bank_file_loc = self.SIGNATURE_FILE_LOC

        self.circle = self.parse_circle_balances(circle_file_loc)
        self.signet = self.parse_signature_bank_balances(signature_bank_file_loc)

        self.portfolio = pd.concat([self.signet, self.circle, self.portfolio])

    def parse_circle_balances(self, circle_file_loc):
        circle = pd.read_excel(circle_file_loc)
        circle = circle[circle['status'] == 'complete']
        circle.loc[circle['transaction_type'].isin(['On-chain Send', 'Wire Withdrawal']), 'amount'] *= -1
        circle['date'] = pd.to_datetime(circle['date'])
        circle['date'] = circle['date'].map(lambda date: date + datetime.timedelta(hours=8, minutes=59))
        circle['date'] = circle['date'].dt.floor('D')
        circle = circle.groupby('date')['amount'].sum().reset_index()
        circle['Position'] = circle['amount'].cumsum()

        circle.rename(columns={'date': 'Date'}, inplace=True)
        circle['Date'] = circle['Date'].map(lambda date: str(date).split(" ")[0])
        circle['Chain'] = np.nan
        circle['Dapp'] = 'Circle Account'
        circle['Pool'] = np.nan
        circle['Token'] = 'USDC'
        circle['Price'] = 1
        circle['USD Value'] = circle['Position'] * circle['Price']

        portfolio_dates = sorted(list(set(self.portfolio['Date'])))
        circle = circle.set_index('Date')
        circle = circle.reindex(portfolio_dates, method='ffill')
        circle = circle.rename_axis('Date').reset_index()

        circle = circle[['Date', 'Chain', 'Dapp', 'Pool', 'Token', 'Position', 'Price', 'USD Value']]

        return circle

    def parse_signature_bank_balances(self, signature_bank_file_loc):
        signet = pd.read_csv(signature_bank_file_loc)
        signet = signet[signet['Transaction Type'] == 'LEDGER']
        signet['Position'] = signet['Summary'].map(lambda amount: float(amount.strip("$")))

        signet['Chain'] = np.nan
        signet['Dapp'] = 'Signature Bank Account'
        signet['Pool'] = np.nan
        signet['Token'] = 'USD'
        signet['Price'] = 1
        signet['USD Value'] = signet['Position'] * signet['Price']

        signet['Post Date'] = pd.to_datetime(signet['Post Date'])

        idx = pd.date_range(signet['Post Date'].iloc[0], signet['Post Date'].iloc[-1], freq="D")
        signet = signet.set_index('Post Date')
        signet = signet.reindex(idx, method='ffill')
        signet = signet.rename_axis('Date').reset_index()

        signet['Date'] = signet['Date'].map(lambda date: datetime.datetime.strftime(date, "%Y-%m-%d"))

        signet = signet[signet['Date'].isin(self.portfolio['Date'])]
        #signet['Position'].fillna(0, inplace=True)

        signet = signet[['Date', 'Chain', 'Dapp', 'Pool', 'Token', 'Position', 'Price', 'USD Value']]

        return signet


port = DeBankPortfolio()

pool = port.get_pool_weights()
print(" ")


