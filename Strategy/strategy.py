import time

from Contract.Contracts import contract_withdrawal
from DB.db import NFTDatabase
from Lending.aave import AAVE
from Utils.EVMutils import EVM
from config import private_key, amount0, name_pools, percentages_, min_tick, sleep_range, low_buy, proxy
from Log.Loging import log
from main import check_pool_tick, calculation_tick, check_amount1, addresses_pools, pool_token, clear_nft, mint, \
    check_id_nft, deposit_withdraw_nft, test_withdraw
from DEX.ODOS import swap
from UNI.Uniswap import UniSwap

from web3.exceptions import ContractLogicError


def check_nft():
    web3, contact = contract_withdrawal('pool_nft', name_pools)
    wallet = web3.eth.account.from_key(private_key).address
    try:
        id_nft = contact.functions.stakedByIndex(wallet, 0).call()
        return id_nft
    except ContractLogicError:
        pass
    _, contract_nft = contract_withdrawal('nft')
    balance_nft = contract_nft.functions.balanceOf(wallet).call()
    if balance_nft > 1:
        raise 'More than 1 NFT, close the extra positions'
    elif balance_nft == 1:
        id_nft = contract_nft.functions.tokenOfOwnerByIndex(wallet, 0).call()
        return id_nft
    else:
        return None


def check_tick(tick_high, low_tick, initial_tick=None, first_pass=False):
    pool_tick = check_pool_tick(name_pools)[1]
    log().info(f'pool tick: {pool_tick} | high tick: {tick_high} {"| " + str(initial_tick) if initial_tick else ""}')
    if pool_tick >= tick_high:
        return False, 1
    elif initial_tick and first_pass:
        if initial_tick + min_tick * -100 >= pool_tick:
            return False, 2
        elif pool_tick <= low_tick:
            return False, 3
        else:
            return True, 0
    elif pool_tick <= low_tick and low_buy:
        return False, 3

    else:
        return True, 0


def lending_strategy(Uni=False):
    lending_aave = AAVE(private_key)
    pool_tick = check_pool_tick(name_pools)
    initial_tick = pool_tick[1]
    uni_swap = UniSwap(proxy)
    first_pass = False
    while True:
        nft_ = check_nft()
        db = NFTDatabase()
        if nft_:
            check_ = db.get_nft_by_id(nft_)
        else:
            check_ = None
        if not check_:
            pool_tick = check_pool_tick(name_pools)
            if Uni:
                uni_swap.mint()
                tick_high, tick_low = uni_swap.calculation_tick(pool_tick[1], percentages_)
                nft_id = uni_swap.check_id_nft()
            else:
                mint(amount0, private_key, name_pools)
                tick_high, tick_low = calculation_tick(pool_tick[1], percentages_)
                nft_id = check_id_nft(private_key)
            if nft_id:
                db = NFTDatabase()
                db.add_nft(nft_id, initial_tick, tick_high, tick_low, first_pass)
                if not Uni:
                    deposit_withdraw_nft(nft_id, private_key, name_pools)
        else:
            log().info(
                f"Найден NFT: id={check_.nft_id}, initial_tick={check_.initial_tick}, high_tick={check_.high_tick},"
                f" low={check_.low_tick}, first_pass={check_.replay}")
            nft_id = nft_
            tick_high, tick_low = check_.high_tick, check_.low_tick
            first_pass = check_.replay
            initial_tick = check_.initial_tick

        time.sleep(2)
        ticker = True
        end_ticker = 0
        while ticker:
            ticker, end_ticker = check_tick(tick_high, tick_low, initial_tick, first_pass)
            if ticker:
                time.sleep(100)
        time.sleep(10)
        if Uni:
            uni_swap.test_withdraw(nft_id)
        else:
            test_withdraw(nft_id, name_pools)
        time.sleep(5)
        balance_WETH, _ = EVM.check_balance(private_key, 'base', lending_aave.tokens['WETH'])
        pool_tick = check_pool_tick(name_pools)
        if end_ticker == 2:
            log().info('swap end WETH -> USDC')
            swap(lending_aave.tokens['WETH'], lending_aave.tokens['USDC'], balance_WETH)
            if lending_aave.user_data()[1]:
                lending_aave.func_contract(1, 'USDC', 'repay')
            break
        elif end_ticker == 3:
            if sleep_range[1]:
                log().info(f'SLEEP {sleep_range[1]} sek')
                time.sleep(sleep_range[1])
            if balance_WETH / 10 ** 18 > amount0:
                log().info('swap WETH -> USDC')
                swap(lending_aave.tokens['WETH'], lending_aave.tokens['USDC'], int(balance_WETH - amount0 * 10 ** 18))
        else:
            if sleep_range[0]:
                log().info(f'SLEEP {sleep_range[0]} sek')
                time.sleep(sleep_range[0])
            if balance_WETH < amount0 * 10 ** 18:
                amount_swap = int(((amount0 - balance_WETH / 10 ** 18) * EVM.get_prices('ETH') * 1.01) * 10 ** 6)
                log().info('swap USDC -> WETH')
                log().info(amount_swap)
                if amount_swap > 10 * 10 ** 6:
                    swap(lending_aave.tokens['USDC'], lending_aave.tokens['WETH'], amount_swap)
            if pool_tick[1] < initial_tick:
                first_pass = True
        time.sleep(3)
