import time

from Contract.Contracts import contract_withdrawal
from DB.db import NFTDatabase
from DEX.UniSwapRouter import UniRouter
from Lending.aave import AAVE
from Utils.EVMutils import EVM
from config import private_key, amount0, name_pools, percentages_, min_tick, sleep_range, low_buy, constant_cycle, \
    low_sale
from Log.Loging import log
from DeFI.aerodrome import check_pool_tick, calculation_tick, mint, \
    check_id_nft, deposit_withdraw_nft, test_withdraw
from DEX.ODOS import swap
from DeFI.Uniswap import UniSwap

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


def check_tick(tick_high, low_tick, initial_tick=None, first_pass=False, uni=None, uni_v4=None):
    if uni:
        pool_tick = uni.check_pool_tick(name_pools)[1]
    elif uni_v4:
        pool_tick, _ = uni_v4.check_ticket_V4()
    else:
        pool_tick = check_pool_tick(name_pools)[1]
    log().info(f'pool tick: {pool_tick} | high tick: {tick_high} {"| " + str(initial_tick) if initial_tick else ""}')
    if pool_tick >= tick_high:
        return False, 1
    elif initial_tick and first_pass and not low_sale:
        if initial_tick + min_tick * -100 >= pool_tick and not constant_cycle:
            return False, 2
        elif pool_tick <= low_tick and not low_sale:
            return False, 3
        else:
            return True, 0
    elif pool_tick <= low_tick and low_buy:
        return False, 3

    else:
        return True, 0


def lending_strategy_aero(Uni=False):
    lending_aave = AAVE(private_key)
    pool_tick = check_pool_tick(name_pools)
    initial_tick = pool_tick[1]
    uni_swap = UniSwap()
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
            swap(lending_aave.tokens['WETH'], lending_aave.tokens['USDC'], balance_WETH, 'base')
            if lending_aave.user_data()[1]:
                lending_aave.func_contract(1, 'USDC', 'repay')
            break
        elif end_ticker == 3:
            if sleep_range[1]:
                log().info(f'SLEEP {sleep_range[1]} sek')
                time.sleep(sleep_range[1])
            if balance_WETH / 10 ** 18 > amount0:
                log().info('swap WETH -> USDC')
                swap(lending_aave.tokens['WETH'], lending_aave.tokens['USDC'], int(balance_WETH - amount0 * 10 ** 18),
                     'base')
        else:
            if sleep_range[0]:
                log().info(f'SLEEP {sleep_range[0]} sek')
                time.sleep(sleep_range[0])
            if balance_WETH < amount0 * 10 ** 18:
                amount_swap = int(((amount0 - balance_WETH / 10 ** 18) * EVM.get_prices('ETH') * 1.01) * 10 ** 6)
                log().info('swap USDC -> WETH')
                log().info(amount_swap)
                if amount_swap > 10 * 10 ** 6:
                    swap(lending_aave.tokens['USDC'], lending_aave.tokens['WETH'], amount_swap, 'base')
            if pool_tick[1] < initial_tick:
                first_pass = True
        time.sleep(3)


def lending_strategy_uni():
    uni_swap = UniSwap()
    lending_aave = AAVE(private_key)
    pool_tick = uni_swap.check_pool_tick(name_pools)
    initial_tick = pool_tick[1]
    first_pass = False
    while True:
        nft_ = uni_swap.check_id_nft()
        db = NFTDatabase()
        if nft_:
            check_ = db.get_nft_by_id(nft_)
        else:
            check_ = None
        if not check_:
            pool_tick = uni_swap.check_pool_tick(name_pools)
            uni_swap.mint()
            tick_high, tick_low = uni_swap.calculation_tick(pool_tick[1], percentages_)
            nft_id = uni_swap.check_id_nft()
            if nft_id:
                db = NFTDatabase()
                db.add_nft(nft_id, initial_tick, tick_high, tick_low, first_pass)
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
            ticker, end_ticker = check_tick(tick_high, tick_low, initial_tick, first_pass, uni_swap)
            if ticker:
                time.sleep(100)
        time.sleep(10)
        uni_swap.test_withdraw(nft_id)
        time.sleep(5)
        balance_WETH, _ = EVM.check_balance(private_key, uni_swap.chain[name_pools],
                                            uni_swap.pool_token[name_pools][0][0])
        pool_tick = uni_swap.check_pool_tick(name_pools)
        if end_ticker == 2:
            log().info('swap end WETH -> USDC')
            swap(uni_swap.pool_token[name_pools][0][0], uni_swap.pool_token[name_pools][1][0],
                 balance_WETH, uni_swap.chain[name_pools])
            if lending_aave.user_data()[1]:
                lending_aave.func_contract(1, 'USDC', 'repay')
            break
        elif end_ticker == 3:
            if sleep_range[1]:
                log().info(f'SLEEP {sleep_range[1]} sek')
                time.sleep(sleep_range[1])
            if balance_WETH / 10 ** 18 > amount0:
                log().info('swap WETH -> USDC')
                swap(uni_swap.pool_token[name_pools][0][0], uni_swap.pool_token[name_pools][1][0],
                     int(balance_WETH - amount0 * 10 ** 18), uni_swap.chain[name_pools])
        else:
            if sleep_range[0]:
                log().info(f'SLEEP {sleep_range[0]} sek')
                time.sleep(sleep_range[0])
            if balance_WETH < amount0 * 10 ** 18:
                amount_swap = int(((amount0 - balance_WETH / 10 ** 18) * EVM.get_prices('ETH') * 1.01) * 10 ** 6)
                log().info('swap USDC -> WETH')
                log().info(amount_swap)
                if amount_swap > 10 * 10 ** 6:
                    swap(uni_swap.pool_token[name_pools][1][0], uni_swap.pool_token[name_pools][0][0], amount_swap,
                         uni_swap.chain[name_pools])
            if pool_tick[1] < initial_tick:
                first_pass = True
        time.sleep(3)


def strategy_uni_V4():
    uni_swap = UniSwap()
    uni_router = UniRouter()
    lending_aave = AAVE(private_key)
    pool_tick, _ = uni_swap.check_ticket_V4()
    initial_tick = pool_tick
    first_pass = False
    while True:
        # nft_ = uni_swap.check_id_V4()
        # db = NFTDatabase()
        # if nft_:
        #     check_ = db.get_nft_by_id(nft_)
        # else:
        #     check_ = None
        # if not check_:
        pool_tick, tick_spacing = uni_swap.check_ticket_V4()
        nft_id = uni_swap.mint_V4()
        tick_high, tick_low = uni_swap.calculation_tick_V4(pool_tick, tick_spacing)
            # nft_id = uni_swap.check_id_nft()
            # if nft_id:
            #     db = NFTDatabase()
            #     db.add_nft(nft_id, initial_tick, tick_high, tick_low, first_pass)
        # else:
        #     log().info(
        #         f"Найден NFT: id={check_.nft_id}, initial_tick={check_.initial_tick}, high_tick={check_.high_tick},"
        #         f" low={check_.low_tick}, first_pass={check_.replay}")
        #     nft_id = nft_
        #     tick_high, tick_low = check_.high_tick, check_.low_tick
        #     first_pass = check_.replay
        #     initial_tick = check_.initial_tick
        #     _, tick_spacing = uni_swap.check_ticket_V4()


        time.sleep(2)
        ticker = True
        end_ticker = 0
        while ticker:
            ticker, end_ticker = check_tick(tick_high, tick_low, initial_tick, first_pass, uni_v4=uni_swap)
            if ticker:
                time.sleep(100)
        time.sleep(10)
        uni_swap.decrease_liquidity(nft_id, tick_low, tick_high, tick_spacing, )
        time.sleep(5)
        token_0 = uni_swap.uni_V4[name_pools][0] if (uni_swap.uni_V4[name_pools][0] !=
                                                     '0x0000000000000000000000000000000000000000') else ''
        balance_0, decimal_0 = EVM.check_balance(private_key, 'uni',  token_0)
        pool_tick, _ = uni_swap.check_ticket_V4()
        name_token = name_pools.split('-')
        if end_ticker == 2:
            log().info(f'The final exchange | {name_token[0]} -> {name_token[1]}')
            uni_router.swap(uni_router.uni_V4[name_pools][0], uni_router.uni_V4[name_pools][1], int(balance_0 * 0.995))
            # if lending_aave.user_data()[1]:
            #     lending_aave.func_contract(1, 'USDC', 'repay')
            break
        elif end_ticker == 3:
            if sleep_range[1]:
                log().info(f'SLEEP {sleep_range[1]} sek')
                time.sleep(sleep_range[1])
                balance_0, _ = EVM.check_balance(private_key, 'uni', token_0)
            if balance_0 / 10 ** decimal_0 > amount0:
                log().info(f'Swap | {name_token[0]} -> {name_token[1]}')
                uni_router.swap(uni_swap.uni_V4[name_pools][0], uni_swap.uni_V4[name_pools][1],
                                int(balance_0 - amount0 * 10 ** decimal_0))
        else:
            if sleep_range[0]:
                log().info(f'SLEEP {sleep_range[0]} sek')
                time.sleep(sleep_range[0])
                balance_0, _ = EVM.check_balance(private_key, 'uni', token_0)
            if balance_0 < amount0 * 10 ** decimal_0:
                amount_swap = int(amount0 * 10 ** decimal_0 - balance_0)
                log().info(f'Swap | {name_token[1]} -> {name_token[0]}')
                log().info(amount_swap)
                if amount_swap > 0.0001 * 10 ** decimal_0:
                    uni_router.swap(uni_swap.uni_V4[name_pools][1], uni_swap.uni_V4[name_pools][0], 0,
                                    amount_swap)
            if pool_tick < initial_tick:
                first_pass = True
        time.sleep(3)


def burn_uni():
    uni = UniSwap()
    while True:
        id_nft, liquidity = uni.check_id_nft(True)
        if id_nft:
            if liquidity:
                uni.test_withdraw(id_nft)
            else:
                uni.burn_nft(id_nft)
        else:
            break
        time.sleep(5)
