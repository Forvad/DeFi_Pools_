import time

from Abi.abi import open_abi
from Utils.EVMutils import EVM
from web3 import Web3
from Log.Loging import log
from config import percentages_, slippage, amount0, processingTime, private_key, name_pools


addresses_pools = {'ETH-USDC': '0xb2cc224c1c9feE385f8ad6a55b4d94E92359DC59'}
pool_token = {'ETH-USDC': [['0x4200000000000000000000000000000000000006', '0x827922686190790b37229fd06084350E74485b72'],
                           ['0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913', '0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43']]}
address_nft = {'ETH-USDC': '0x827922686190790b37229fd06084350E74485b72'}

pool_nft = {'ETH-USDC': '0xF33a96b5932D9E9B9A0eDA447AbD8C9d48d2e0c8'}

# percentages_ = [1, 1]  # hiht, low
#
# amount0 = 0.01
#
# slippage = 5  # %

# 7063840


def check_pool_tick(address_pool):
    web3 = EVM.web3('base')

    contract = web3.eth.contract(address=Web3.to_checksum_address(address_pool),
                                         abi=open_abi()['ETH-USD'])
    return contract.functions.slot0().call()


def check_amount1(pool_tick, tickLow, tickHigh, value, address_pool):
    web3 = EVM.web3('base')
    contract = web3.eth.contract(address=Web3.to_checksum_address('0x0AD09A66af0154a84e86F761313d02d0abB6edd5'),
                                 abi=open_abi()['chek_pool'])
    return contract.functions.estimateAmount1(value,
                                              address_pool,
                                              pool_tick[0],
                                              tickLow,
                                              tickHigh).call()


def calculation_tick(pool_tick, percentages):
    for i in percentages:
        if i < 1:
            raise 'Процент должен быть выше 1'
    tick_high, tick_low = pool_tick + pool_tick * -1 % 100, pool_tick - (100 - pool_tick * -1 % 100) - 100
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
    web3 = EVM.web3('base')
    wallet = web3.eth.account.from_key(private_key).address
    for i in pool_token[name_poll]:
        EVM.approve(amount, private_key, 'base', i[0], i[1])
    pool_tick = check_pool_tick(addresses_pools[name_poll])
    tick_high, tick_low = calculation_tick(pool_tick[1], percentages_)
    contract = web3.eth.contract(address=Web3.to_checksum_address(address_nft[name_poll]),
                                 abi=open_abi()['nft'])
    amount1_ = check_amount1(pool_tick, tick_low, tick_high, int(amount0_), addresses_pools[name_poll])
    tx = contract.functions.mint((pool_token[name_poll][0][0],
                                 pool_token[name_poll][1][0],
                                 100,
                                 tick_low,
                                 tick_high,
                                 amount0_,
                                 amount1_,
                                 int(amount0_ * (1 - slippage / 100)),
                                 int(amount1_ * (1 - slippage / 100)),
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
    module_str = 'Минтим NFT'
    tx_bool = EVM.sending_tx(web3, tx, 'base', private_key, 1, module_str)
    if not tx_bool:
        log().error('Зафейлилась транза')
        time.sleep(30)
        if retry <= 3:
            return mint(amount, private_key, name_poll, retry + 1)
        else:
            raise 'Не получается заминтить НФТ'

    else:
        return True


def approve_NFT(private_key, name_poll, retry=0):
    web3 = EVM.web3('base')
    wallet = web3.eth.account.from_key(private_key).address
    contract = web3.eth.contract(address=Web3.to_checksum_address(address_nft[name_poll]),
                                 abi=open_abi()['nft'])
    id_nft = check_id_nft(private_key, name_poll)
    if id_nft:
        tx = contract.functions.approve(pool_nft[name_poll], id_nft).build_transaction({
            'from': wallet,
            'nonce': web3.eth.get_transaction_count(wallet),
            'chainId': web3.eth.chain_id,
            'gasPrice': web3.eth.gas_price,
            'gas': 0
        })
        module_str = 'Делаем апрув NFT'
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
    web3 = EVM.web3('base')
    wallet = web3.eth.account.from_key(private_key).address
    contract = web3.eth.contract(address=Web3.to_checksum_address(pool_nft[name_poll]),
                                 abi=open_abi()['pool_nft'])
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
    module_str = 'Стейкаем / Выводим NFT'
    tx_bool = EVM.sending_tx(web3, tx, 'base', private_key, 1, module_str)
    if not tx_bool:
        log().error('Зафейлилась транза')
        time.sleep(5)
        if retry <= 3:
            return deposit_withdraw_nft(id_nft, private_key, name_poll, withdraw, retry + 1)
        else:
            raise 'Не получается задепозитить либо вывести'
    else:
        return True


def decreaseLiquidity(id_nft, private_key, name_poll, retry=0):
    check_nft = check_id_nft(private_key, name_poll)
    if not check_nft == id_nft:
        deposit_withdraw_nft(id_nft, private_key, name_pools, True)
        time.sleep(2)
    web3 = EVM.web3('base')
    max_token = int(10 * 10 ** 25)
    wallet = web3.eth.account.from_key(private_key).address
    contract = web3.eth.contract(address=Web3.to_checksum_address(address_nft[name_poll]),
                                 abi=open_abi()['nft'])
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
    web3 = EVM.web3('base')
    max_token = int(10 * 10 ** 25)
    wallet = web3.eth.account.from_key(private_key).address
    contract = web3.eth.contract(address=Web3.to_checksum_address(address_nft[name_poll]),
                                 abi=open_abi()['nft'])
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


def check_id_nft(private_key, name_pool):
    web3 = EVM.web3('base')
    wallet = web3.eth.account.from_key(private_key).address
    contract = web3.eth.contract(address=Web3.to_checksum_address(address_nft[name_pool]),
                                 abi=open_abi()['nft'])
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


def auto_():
    while True:
        mint(amount0, private_key, name_pools)
        nft_id = check_id_nft(private_key, name_pools)
        if nft_id:
            time.sleep(2)
            approve_NFT(private_key, name_pools)
            time.sleep(2)
            deposit_withdraw_nft(nft_id, private_key, name_pools)
            time.sleep(2)
            log().info(f'Начинаем фармить ---- 0 / {processingTime[1]} мин')
            time.sleep(processingTime[1] * 60)
            deposit_withdraw_nft(nft_id, private_key, name_pools, True)
            time.sleep(2)
            decreaseLiquidity(nft_id, private_key, name_pools)
            time.sleep(1)
            burn_nft(nft_id, private_key, name_pools)
        log().info(f'Спим до следующего захода ----  0 / {processingTime[0]} мин')
        time.sleep(processingTime[0] * 60)


if __name__ == '__main__':
    auto_()


