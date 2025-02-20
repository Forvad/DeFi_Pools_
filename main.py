import time

from Utils.EVMutils import EVM
from Log.Loging import log
from config import percentages_, slippage, amount0, processingTime, private_key, name_pools, auto_amount
from Contract.Contracts import contract_withdrawal, pool_nft
from web3.exceptions import ContractLogicError


addresses_pools = {'ETH-USDC': '0xb2cc224c1c9feE385f8ad6a55b4d94E92359DC59',
                   'ETH-cbBTC': '0x70aCDF2Ad0bf2402C957154f944c19Ef4e1cbAE1',
                   "VIRTUAL-ETH": "0x3f0296BF652e19bca772EC3dF08b32732F93014A"
                   }
pool_token = {'ETH-USDC': [['0x4200000000000000000000000000000000000006', '0x827922686190790b37229fd06084350E74485b72'],
                           ['0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913', '0x827922686190790b37229fd06084350E74485b72']],
              'ETH-cbBTC': [['0x4200000000000000000000000000000000000006', '0x827922686190790b37229fd06084350E74485b72'],
                            ['0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf', '0x827922686190790b37229fd06084350E74485b72']],
              'VIRTUAL-ETH': [
                  ['0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b', '0x827922686190790b37229fd06084350E74485b72'],
                  ['0x4200000000000000000000000000000000000006', '0x827922686190790b37229fd06084350E74485b72']]
              }


def check_pool_tick(name_pool):
    _, contract = contract_withdrawal(name_pool)
    return contract.functions.slot0().call()


def check_amount1(pool_tick, tickLow, tickHigh, value, address_pool):
    _, contract = contract_withdrawal('check_amount1')
    return contract.functions.estimateAmount1(value,
                                              address_pool,
                                              pool_tick[0],
                                              tickLow,
                                              tickHigh).call()


def check_amount0(pool_tick, tickLow, tickHigh, value, address_pool):
    _, contract = contract_withdrawal('check_amount1')
    return contract.functions.estimateAmount0(value,
                                              address_pool,
                                              pool_tick[0],
                                              tickLow,
                                              tickHigh).call()


def calculation_tick(pool_tick, percentages):
    for i in percentages:
        if i < 1:
            raise 'The percentage must be higher than 1'
    tick_high, tick_low = pool_tick + (pool_tick * -1 % 100), pool_tick - (100 - pool_tick * -1 % 100)
    high = 1
    low = 1
    while True:
        if percentages[0] > high:
            tick_high += 100
            high += 1
        if percentages[1] > low:
            tick_low -= 100
            low += 1
        if percentages[0] == high and percentages[1] == low:
            return tick_high, tick_low


def mint(amount, private_key, name_poll, retry=0):
    amount0_ = int(amount * 10 ** 18)
    web3, contract = contract_withdrawal('nft')
    wallet = web3.eth.account.from_key(private_key).address
    pool_tick = check_pool_tick(name_pools)
    tick_high, tick_low = calculation_tick(pool_tick[1], percentages_)

    amount1_ = check_amount1(pool_tick, tick_low, tick_high, int(amount0_), addresses_pools[name_poll])
    balance_1, decimal1 = EVM.check_balance(private_key, 'base', pool_token[name_poll][0][0])
    balance_2, decimal2 = EVM.check_balance(private_key, 'base', pool_token[name_poll][1][0])
    for i in pool_token[name_poll]:
        if i == 0:
            amounts = amount0_
        else:
            amounts = amount1_
        EVM.approve(amounts, private_key, 'base', i[0], i[1])
    if balance_1 < int(amount0_) or balance_2 < int(amount1_):
        if auto_amount and balance_2 < int(amount1_):
            amount1_ = balance_2
            amount0_ = check_amount0(pool_tick, tick_low, tick_high, int(amount1_), addresses_pools[name_poll])
        else:
            time.sleep(15)
            if auto_amount and balance_1 < int(amount0_):
                amount = round(balance_1 / 10 ** decimal1, 5)
            return mint(amount, private_key, name_poll, retry)
    tx = contract.functions.mint((pool_token[name_poll][0][0],
                                 pool_token[name_poll][1][0],
                                 100,
                                 tick_low,
                                 tick_high,
                                 amount0_,
                                 amount1_,
                                 0,
                                 0,
                                 wallet,
                                 int(time.time()) + 1_000,
                                 0
                                  )).build_transaction({
                                    'from': wallet,
                                    'nonce': web3.eth.get_transaction_count(wallet),
                                    'chainId': web3.eth.chain_id,
                                    'gasPrice': web3.eth.gas_price,
                                    'gas': 0
                                    })
    name = name_pools.split("-")
    module_str = (f'Mint NFT | {pool_tick[1]} / {tick_low} / {tick_high} | {round(amount0_ / 10 ** decimal1, 5)} {name[0]} | '
                  f'{round(amount1_ / 10 **  decimal2, 5)} {name[1]}')
    tx_bool = EVM.sending_tx(web3, tx, 'base', private_key, 1, module_str)
    if not tx_bool:
        log().error('Зафейлилась транза')
        time.sleep(15)
        if retry <= 3:
            return mint(amount, private_key, name_poll, retry + 1)
        else:
            raise 'Не получается заминтить НФТ'

    else:
        return True


def approve_NFT(private_key, name_poll, retry=0):
    web3, contract = contract_withdrawal('nft')
    wallet = web3.eth.account.from_key(private_key).address
    tx = contract.functions.setApprovalForAll(pool_nft[name_poll], True).build_transaction({
        'from': wallet,
        'nonce': web3.eth.get_transaction_count(wallet),
        'chainId': web3.eth.chain_id,
        'gasPrice': web3.eth.gas_price,
        'gas': 0
    })
    module_str = f'Approve the NFT -> {pool_nft[name_poll]}'
    tx_bool = EVM.sending_tx(web3, tx, 'base', private_key, 1, module_str)
    if not tx_bool:
        log().error('Зафейлилась транза')
        time.sleep(5)
        if retry <= 3:
            return approve_NFT(private_key, name_poll, retry + 1)
        else:
            raise 'Не получается сделать апрув'
    else:

        return True


def deposit_withdraw_nft(id_nft, private_key, name_poll, withdraw=False, retry=0):
    web3, contract = contract_withdrawal('pool_nft', name_poll)
    wallet = web3.eth.account.from_key(private_key).address
    if not withdraw:
        tx = contract.functions.deposit(id_nft)
    else:
        tx = contract.functions.withdraw(id_nft)

    tx = tx.build_transaction({
        'from': wallet,
        'nonce': web3.eth.get_transaction_count(wallet),
        'chainId': web3.eth.chain_id,
        'gasPrice': web3.eth.gas_price,
        'gas': 0
    })
    module_str = 'Stake NFT' if not withdraw else "Withdraw NFT"
    tx_bool = EVM.sending_tx(web3, tx, 'base', private_key, 1, module_str)
    if not tx_bool:
        log().error('Failed tx')
        time.sleep(5)
        if retry <= 3:
            return deposit_withdraw_nft(id_nft, private_key, name_poll, withdraw, retry + 1)
        else:
            raise 'Unable to deposit or withdraw'
    else:
        return True


def decreaseLiquidity(id_nft, private_key, name_poll, retry=0):
    check_nft = check_id_nft(private_key)
    if not check_nft == id_nft:
        deposit_withdraw_nft(id_nft, private_key, name_pools, True)
        time.sleep(2)
    web3, contract = contract_withdrawal('nft')
    max_token = int(10 * 10 ** 25)
    wallet = web3.eth.account.from_key(private_key).address
    liquidity = int(contract.functions.positions(id_nft).call()[7])
    tx_all = [contract.functions.decreaseLiquidity((id_nft, liquidity, 0, 0, int(time.time()) + 1_000)),
              contract.functions.collect((id_nft, wallet, max_token, max_token))
              ]
    bytes_tx = []

    for tx in tx_all:

        bytes_tx.append(tx.build_transaction({
            'from': wallet,
            'nonce': web3.eth.get_transaction_count(wallet),
            'chainId': web3.eth.chain_id,
            'gasPrice': web3.eth.gas_price,
            'gas': 0
        })['data'])
    tx = contract.functions.multicall(bytes_tx).build_transaction({
            'from': wallet,
            'nonce': web3.eth.get_transaction_count(wallet),
            'chainId': web3.eth.chain_id,
            'gasPrice': web3.eth.gas_price,
            'gas': 0
        })
    module_str = 'Достаём ликвидность и клеймим награды'
    tx_bool = EVM.sending_tx(web3, tx, 'base', private_key, 1, module_str)
    if not tx_bool:
        time.sleep(5)
        log().error('Зафейлилась транза')
        log().info(bytes_tx)
        if retry <= 3:
            return decreaseLiquidity(id_nft, private_key, name_poll, retry + 1)
        raise 'НЕ смолги достать ликвидность'
    else:
        time.sleep(1)
        liquidity = int(contract.functions.positions(id_nft).call()[7])
        if liquidity > 0:
            return decreaseLiquidity(id_nft, private_key, name_poll, retry)
        return True


def burn_nft(id_nft, private_key, name_poll, retry=0):
    web3, contract = contract_withdrawal('nft')
    max_token = int(10 * 10 ** 25)
    wallet = web3.eth.account.from_key(private_key).address
    tx_all = [contract.functions.collect((id_nft, wallet, max_token, max_token)),
              contract.functions.burn(id_nft)]
    bytes_tx = []

    for tx in tx_all:

        bytes_tx.append(tx.build_transaction({
            'from': wallet,
            'nonce': web3.eth.get_transaction_count(wallet),
            'chainId': web3.eth.chain_id,
            'gasPrice': web3.eth.gas_price,
            'gas': 0
        })['data'])
    tx = contract.functions.multicall(bytes_tx).build_transaction({
            'from': wallet,
            'nonce': web3.eth.get_transaction_count(wallet),
            'chainId': web3.eth.chain_id,
            'gasPrice': web3.eth.gas_price,
            'gas': 0
        })
    module_str = 'Клеймим награды и стераем НФТ'
    tx_bool = EVM.sending_tx(web3, tx, 'base', private_key, 1, module_str)
    if not tx_bool:
        time.sleep(5)
        log().error('Зафейлилась транза')
        if retry <= 3:
            return burn_nft(id_nft, private_key, name_poll, retry + 1)
        raise 'НЕ смолги стереть нфт'
    else:

        return True


def check_id_nft(private_key):
    web3, contract = contract_withdrawal('nft')
    wallet = web3.eth.account.from_key(private_key).address
    balance = contract.functions.balanceOf(wallet).call()
    if balance > 1:
        return None

    elif balance == 1:
        id_nft = contract.functions.tokenOfOwnerByIndex(wallet, balance - 1).call()
        liquid = contract.functions.positions(id_nft).call()[7]
        if liquid > 0:
            return id_nft
        else:
            return None


def clear_nft(private_key_, name_pool):
    web3, contact = contract_withdrawal('pool_nft', name_pool)
    wallet = web3.eth.account.from_key(private_key_).address
    while True:
        try:
            id_nft = contact.functions.stakedByIndex(wallet, 0).call()
            deposit_withdraw_nft(id_nft, private_key_, name_pool, True)
            time.sleep(2)
            test_withdraw(id_nft, name_pool)
            # decreaseLiquidity(id_nft, private_key_, name_pool)
            # time.sleep(1)
            # burn_nft(id_nft, private_key_, name_pool)
            # time.sleep(5)
        except ContractLogicError:
            break
    _, contract_nft = contract_withdrawal('nft')
    balance_nft = contract_nft.functions.balanceOf(wallet).call()
    if balance_nft >= 1:
        for _ in range(balance_nft):
            id_nft = contract_nft.functions.tokenOfOwnerByIndex(wallet, 0).call()
            liquid = contract_nft.functions.positions(id_nft).call()[7]
            if liquid > 0:
                # decreaseLiquidity(id_nft, private_key_, name_pool)
                test_withdraw(id_nft, name_pool)
                time.sleep(1)
            else:
                burn_nft(id_nft, private_key_, name_pool)
                time.sleep(3)


def test_withdraw(id_nft, name_poll, retry=0):
    check_nft = check_id_nft(private_key)
    if not check_nft == id_nft:
        deposit_withdraw_nft(id_nft, private_key, name_pools, True)
        time.sleep(2)
    web3, contract = contract_withdrawal('nft')
    max_token = 340282366920938463463374607431768211455
    wallet = web3.eth.account.from_key(private_key).address
    liquidity = int(contract.functions.positions(id_nft).call()[7])
    tx_all = [contract.functions.decreaseLiquidity((id_nft, liquidity, 0, 0, int(time.time()) + 1_000)),
              contract.functions.collect((id_nft, wallet, max_token, max_token)),
              contract.functions.sweepToken(pool_token[name_poll][0][0], 0, wallet),
              contract.functions.sweepToken(pool_token[name_poll][1][0], 0, wallet),
              contract.functions.burn(id_nft)
              ]
    bytes_tx = []

    for tx in tx_all:
        bytes_tx.append(tx.build_transaction({
            'from': wallet,
            'nonce': web3.eth.get_transaction_count(wallet),
            'chainId': web3.eth.chain_id,
            'gasPrice': web3.eth.gas_price,
            'gas': 0
        })['data'])
    tx = contract.functions.multicall(bytes_tx).build_transaction({
        'from': wallet,
        'nonce': web3.eth.get_transaction_count(wallet),
        'chainId': web3.eth.chain_id,
        'gasPrice': web3.eth.gas_price,
        'gas': 0
    })
    module_str = 'Withdraw liquidity, claim rewards, and burn the NFT'
    tx_bool = EVM.sending_tx(web3, tx, 'base', private_key, 1, module_str)
    if not tx_bool:
        time.sleep(5)
        log().error('Filed tx')
        log().info(bytes_tx)
        if retry <= 3:
            return test_withdraw(id_nft, name_poll, retry + 1)
        raise "Couldn't withdraw liquidity"
    else:
        return True


def auto_():
    while True:
        clear_nft(private_key, name_pools)
        time.sleep(3)
        mint(amount0, private_key, name_pools)
        nft_id = check_id_nft(private_key)
        if nft_id:
            time.sleep(2)
            deposit_withdraw_nft(nft_id, private_key, name_pools)
            time.sleep(2)
            log().info(f'Farm for {processingTime[1]} seconds')
            time.sleep(processingTime[1])
            deposit_withdraw_nft(nft_id, private_key, name_pools, True)
            time.sleep(2)
            test_withdraw(nft_id, name_pools)
        log().info(f'Sleep for {processingTime[0]} seconds')
        log().success(f"{'-' * 50}//{'-' * 50}")
        time.sleep(processingTime[0])


if __name__ == '__main__':
    print(calculation_tick(-266132, [1, 1]))


