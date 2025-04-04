import random
import time

import requests

from Utils.EVMutils import EVM
from Log.Loging import log, inv_log
from config import (percentages_,  amount0, processingTime, private_key, name_pools, auto_amount, random_sleep,
                    random_sleep_)
from Contract.Contracts import contract_withdrawal, pool_nft
from web3.exceptions import ContractLogicError


class UniSwap:
    addresses_pools = {'ETH-USDC': '0xd0b53D9277642d899DF5C87A3966A349A798F224'
                       }
    pool_token = {'ETH-USDC': [['0x4200000000000000000000000000000000000006', '0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1'],
                               ['0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913', '0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1']],
                  'ETH-cbBTC': [['0x4200000000000000000000000000000000000006', '0x827922686190790b37229fd06084350E74485b72'],
                                ['0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf', '0x827922686190790b37229fd06084350E74485b72']],
                  'VIRTUAL-ETH': [
                      ['0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b', '0x827922686190790b37229fd06084350E74485b72'],
                      ['0x4200000000000000000000000000000000000006', '0x827922686190790b37229fd06084350E74485b72']]
                  }

    def __init__(self, proxy=None):
        self.proxy = proxy
        self.session = requests.Session()
        if self.proxy:
            self.session.proxies.update({
                'http': self.proxy,
                'https': self.proxy
            })

    def check_pool_tick(self, name_pool):
        try:
            _, contract = contract_withdrawal(name_pool)
            return contract.functions.slot0().call()
        except BaseException as error:
            log().error(error)
            time.sleep(10)
            return self.check_pool_tick(name_pool)

    @staticmethod
    def check_amount1(pool_tick, tickLow, tickHigh, value, address_pool):
        _, contract = contract_withdrawal('check_amount1')
        return contract.functions.estimateAmount1(value,
                                                  address_pool,
                                                  pool_tick[0],
                                                  tickLow,
                                                  tickHigh).call()

    @staticmethod
    def check_amount0(pool_tick, tickLow, tickHigh, value, address_pool):
        _, contract = contract_withdrawal('check_amount1')
        return contract.functions.estimateAmount0(value,
                                                  address_pool,
                                                  pool_tick[0],
                                                  tickLow,
                                                  tickHigh).call()

    @staticmethod
    def calculation_tick(pool_tick, percentages):
        pool_tick -= pool_tick % 10
        for i in percentages:
            if i < 0.1:
                raise 'The percentage must be higher than 0.1'
        return int(pool_tick + percentages[1] * 100), int(pool_tick - percentages[1] * 100)

    @staticmethod
    def check_id_nft():
        web3, contract = contract_withdrawal('nft_uni')
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

    def mint(self, retry=0):
        amount0_ = int(amount0 * 10 ** 18)
        web3, contract = contract_withdrawal('nft_uni')
        wallet = web3.eth.account.from_key(private_key).address
        pool_tick = self.check_pool_tick(name_pools)
        tick_high, tick_low = self.calculation_tick(pool_tick[1], percentages_)
        amount1_ = self.check_amount1(pool_tick, tick_low, tick_high, int(amount0_), self.addresses_pools[name_pools])
        balance_1, decimal1 = EVM.check_balance(private_key, 'base', self.pool_token[name_pools][0][0])
        balance_2, decimal2 = EVM.check_balance(private_key, 'base', self.pool_token[name_pools][1][0])
        for i in self.pool_token[name_pools]:
            if i == 0:
                amounts = amount0_
            else:
                amounts = amount1_
            EVM.approve(amounts, private_key, 'base', i[0], i[1])
        if balance_1 < int(amount0_) or balance_2 < int(amount1_):
            inv_log().info("Нехватаа баланса, ищем способ решения")
            if auto_amount and balance_2 < int(amount1_):
                inv_log().info("не жостаточно 2 монеты переварачиваем")
                amount1_ = balance_2
                amount0_ = self.check_amount0(pool_tick, tick_low, tick_high, int(amount1_),
                                              self.addresses_pools[name_pools])
            elif auto_amount and balance_1 < int(amount0_):
                inv_log().info("не жостаточно 1, ставим сколько имеется")
                amount0_ = balance_1
            else:
                raise "Минт крашнулся"
        # while True:
        #     data = self.create_tx(tick_low, tick_high, wallet)
        #     if data.get("create"):
        #         break
        #     else:
        #         log().error(data)
        #         time.sleep(10)
        #
        # tx = {
        #     "data": data["create"]["data"],
        #     "to": data["create"]["to"],
        #     'from': wallet,
        #         'nonce': web3.eth.get_transaction_count(wallet),
        #         'chainId': web3.eth.chain_id,
        #         'gasPrice': web3.eth.gas_price,
        #         'gas': 0
        # }
        tx = contract.functions.mint((self.pool_token[name_pools][0][0],
                                      self.pool_token[name_pools][1][0],
                                      500,
                                      tick_low,
                                      tick_high,
                                      amount0_,
                                      amount1_,
                                      0,
                                      0,
                                      wallet,
                                      int(time.time()) + 1_000
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
            if retry <= 5:
                return self.mint(retry + 1)
            else:
                raise 'Не получается заминтить НФТ'

        else:
            return pool_tick[1]

    def create_tx(self, tick_low, tick_high, address) -> dict:
        try:
            headers = {
                'accept': '*/*',
                'accept-language': 'ru,en;q=0.9,ru-BY;q=0.8,ru-RU;q=0.7,en-US;q=0.6',
                'content-type': 'application/json',
                'origin': 'https://app.uniswap.org',
                'priority': 'u=1, i',
                'referer': 'https://app.uniswap.org/',
                'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                              ' Chrome/134.0.0.0 Safari/537.36',
                'x-api-key': 'JoyCGj29tT4pymvhaGciK4r1aIPvqW6W53xT1fwo',
                'x-app-version': '',
                'x-request-source': 'uniswap-web',
            }

            json_data = {
                'simulateTransaction': True,
                'protocol': 'V3',
                'walletAddress': address,
                'chainId': 8453,
                'independentAmount': f'{int(amount0 * 10 ** 18)}',
                'independentToken': 'TOKEN_0',
                'position': {
                    'tickLower': tick_low,
                    'tickUpper': tick_high,
                    'pool': {
                        'tickSpacing': 10,
                        'token0': self.pool_token[name_pools][0][0],
                        'token1': self.pool_token[name_pools][1][0],
                        'fee': 500,
                    },
                },
            }

            response = self.session.post('https://trading-api-labs.interface.gateway.uniswap.org/v1/lp/create',
                                         headers=headers, json=json_data)
            return response.json()
        except BaseException as error:
            log().error(error)
            time.sleep(20)
            return self.create_tx(tick_low, tick_high, address)

    def test_withdraw(self, id_nft, retry=0):
        web3, contract = contract_withdrawal('nft_uni')
        max_token = 340282366920938463463374607431768211455
        wallet = web3.eth.account.from_key(private_key).address
        liquidity = int(contract.functions.positions(id_nft).call()[7])
        tx_all = [
                  contract.functions.decreaseLiquidity((id_nft, liquidity, 0, 0, int(time.time()) + 1_000)),
                  contract.functions.collect((id_nft, wallet, max_token, max_token)),
                  contract.functions.sweepToken(self.pool_token[name_pools][0][0], 0, wallet),
                  contract.functions.sweepToken(self.pool_token[name_pools][1][0], 0, wallet),
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
            if retry <= 3:
                return self.test_withdraw(id_nft, retry + 1)
            raise "Couldn't withdraw liquidity"
        else:
            return True

    def burn_nft(self, id_nft, retry=0):
        web3, contract = contract_withdrawal('nft_uni')
        max_token = int(10 * 10 ** 25)
        wallet = web3.eth.account.from_key(private_key).address
        # tx_all = [contract.functions.collect((id_nft, wallet, max_token, max_token)),
        #           contract.functions.burn(id_nft)]
        # bytes_tx = []
        #
        # for tx in tx_all:
        #     bytes_tx.append(tx.build_transaction({
        #         'from': wallet,
        #         'nonce': web3.eth.get_transaction_count(wallet),
        #         'chainId': web3.eth.chain_id,
        #         'gasPrice': web3.eth.gas_price,
        #         'gas': 0
        #     })['data'])
        # tx = contract.functions.multicall(bytes_tx).build_transaction({
        #     'from': wallet,
        #     'nonce': web3.eth.get_transaction_count(wallet),
        #     'chainId': web3.eth.chain_id,
        #     'gasPrice': web3.eth.gas_price,
        #     'gas': 0
        # })
        tx = contract.functions.burn(id_nft).build_transaction({
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
                return self.burn_nft(id_nft, retry + 1)
            raise 'НЕ смолги стереть нфт'
        else:

            return True
