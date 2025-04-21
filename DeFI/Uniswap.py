import time

import requests
from web3 import Web3

from Utils.EVMutils import EVM
from Log.Loging import log, inv_log
from config import percentages_,  amount0, private_key, name_pools, auto_amount, proxy
from Contract.Contracts import contract_withdrawal
from web3.exceptions import ContractLogicError


class UniSwap:
    chain = {
        'ETH-USDC-base': 'base',
        'ETH-USDC-arb': 'arbitrum',
        'ETH-USDC-eth': 'ethereum'
    }
    addresses_pools = {'ETH-USDC-base': '0xd0b53D9277642d899DF5C87A3966A349A798F224',
                       'ETH-USDC-arb': '0xC6962004f452bE9203591991D15f6b388e09E8D0',
                       'ETH-USDC-eth': '0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640'
                       }
    pool_token = {'ETH-USDC-base': [
        [
            '0x4200000000000000000000000000000000000006',
            '0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1'
         ],
        [
            '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
            '0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1'
        ],
    ],
            'ETH-USDC-arb': [
                [
                    '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
                    '0xC36442b4a4522E871399CD717aBDD847Ab11FE88'
                ],
                [
                    '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
                    '0xC36442b4a4522E871399CD717aBDD847Ab11FE88'
                ],
            ],
            'ETH-USDC-eth': [
            [
                '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
                '0xC36442b4a4522E871399CD717aBDD847Ab11FE88'
            ],
            [
                '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
                '0xC36442b4a4522E871399CD717aBDD847Ab11FE88'
            ],
        ],
                  }
    fee_pool = {'ETH-wstETH-uni': 100, 'USDC-WBTC-uni': 3000, 'USDT-WBTC-uni': 500}
    uni_V4 = {'ETH-wstETH-uni': ['0x0000000000000000000000000000000000000000',
                                 '0xc02fe7317d4eb8753a02c35fe019786854a92001'],
              'USDC-WBTC-uni': ['0x078D782b760474a361dDA0AF3839290b0EF57AD6',
                                '0x927B51f251480a681271180DA4de28D44EC4AfB8'],
              'USDT-WBTC-uni': ['0x9151434b16b9763660705744891fA906F660EcC5',
                                '0x927B51f251480a681271180DA4de28D44EC4AfB8']}

    def __init__(self):
        self.session = requests.Session()
        if proxy:
            self.session.proxies.update({
                'http': proxy,
                'https': proxy
            })
        self.web3, _ = contract_withdrawal('nft_uni')
        self.wallet = self.web3.eth.account.from_key(private_key).address
        self.session.headers = {
            'accept': '*/*',
            'accept-language': 'ru,en;q=0.9,ru-BY;q=0.8,ru-RU;q=0.7,en-US;q=0.6',
            'content-type': 'application/json',
            'origin': 'https://app.uniswap.org',
            'priority': 'u=1, i',
            'referer': 'https://app.uniswap.org/',
            'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/135.0.0.0 Safari/537.36',
            'x-api-key': 'JoyCGj29tT4pymvhaGciK4r1aIPvqW6W53xT1fwo',
            'x-app-version': '',
            'x-request-source': 'uniswap-web',
            'x-universal-router-version': '2.0'
        }

    def check_pool_tick(self, name_pool):
        try:
            _, contract = contract_withdrawal('ETH-USDC')
            return contract.functions.slot0().call()
        except BaseException as error:
            log().error(error)
            time.sleep(10)
            return self.check_pool_tick(name_pool)

    @staticmethod
    def check_amount1(pool_tick, tickLow, tickHigh, value):
        address_pool = UniSwap.addresses_pools['ETH-USDC-base']
        _, contract = contract_withdrawal('check_amount1')
        return contract.functions.estimateAmount1(value,
                                                  address_pool,
                                                  pool_tick[0],
                                                  tickLow,
                                                  tickHigh).call()

    @staticmethod
    def check_amount0(pool_tick, tickLow, tickHigh, value):
        address_pool = UniSwap.addresses_pools['ETH-USDC-base']
        _, contract = contract_withdrawal('check_amount1')
        return contract.functions.estimateAmount0(value,
                                                  address_pool,
                                                  pool_tick[0],
                                                  tickLow,
                                                  tickHigh).call()

    @staticmethod
    def calculation_tick(pool_tick, percentages):
        pool_tick -= pool_tick % 10
        # for i in percentages:
        #     if i < 0.1:
        #         raise 'The percentage must be higher than 0.1'
        return int(pool_tick + percentages[0] * 100), int(pool_tick - percentages[1] * 100)

    @staticmethod
    def calculation_tick_V4(pool_tick, tick_step):
        if tick_step > percentages_[0] * 100 or tick_step > percentages_[1] * 100:
            log().info(f'Шаг слишком маленький для данной пары, нужно от {tick_step / 100}%')
            percentages_[0] = input('ввежите новый high: ')
            percentages_[1] = input('ввежите новый low: ')
        if tick_step == 60:
            pool_tick += (10 - pool_tick % 10) + 10
        elif tick_step >= 10:
            pool_tick += (10 - pool_tick % 10)
        return int(pool_tick + percentages_[0] * 100), int(pool_tick - percentages_[1] * 100)

    @staticmethod
    def check_id_nft(liquidity=False):
        try:
            web3, contract = contract_withdrawal('nft_uni')
            wallet = web3.eth.account.from_key(private_key).address
            balance = contract.functions.balanceOf(wallet).call()
            if balance >= 1:
                if liquidity:
                    id_nft = contract.functions.tokenOfOwnerByIndex(wallet, balance - 1).call()
                    return id_nft, contract.functions.positions(id_nft).call()[7]
                return contract.functions.tokenOfOwnerByIndex(wallet, balance - 1).call()
            if liquidity:
                return None, None
        except BaseException as error:
            log().error(error)
            time.sleep(10)
            return UniSwap.check_id_nft()

    @staticmethod
    def check_id_V4():
        try:
            web3, contract = contract_withdrawal('nft_uni')
            wallet = web3.eth.account.from_key(private_key).address
            end_id = contract.functions.nextTokenId().call()
            for i in range(100):
                search_id = end_id - i
                try:
                    address_end = contract.functions.ownerOf(search_id).call()
                except ContractLogicError:
                    address_end = ''
                if address_end == wallet:
                    return search_id
        except BaseException as error:
            log().error(error)
            time.sleep(10)
            return UniSwap.check_id_V4()

    def mint(self, retry=0):
        try:
            amount0_ = int(amount0 * 10 ** 18)
            _, contract = contract_withdrawal('nft_uni')
            wallet = self.web3.eth.account.from_key(private_key).address
            pool_tick = self.check_pool_tick(name_pools)
            tick_high, tick_low = self.calculation_tick(pool_tick[1], percentages_)
            if pool_tick[1] <= tick_low:
                amount1_ = 0
            else:
                amount1_ = self.check_amount1(pool_tick, tick_low, tick_high, int(amount0_))
            log().info(f'{pool_tick[1], tick_high, tick_low}')
            balance_1, decimal1 = EVM.check_balance(private_key, self.chain[name_pools], self.pool_token[name_pools][0][0])
            balance_2, decimal2 = EVM.check_balance(private_key, self.chain[name_pools], self.pool_token[name_pools][1][0])
            for i in self.pool_token[name_pools]:
                if i == 0:
                    amounts = amount0_
                else:
                    amounts = amount1_
                EVM.approve(amounts, private_key, self.chain[name_pools], i[0], i[1])
            if balance_1 < int(amount0_) or balance_2 < int(amount1_):
                inv_log().info("Нехватаа баланса, ищем способ решения")
                if auto_amount and balance_2 < int(amount1_):
                    inv_log().info("не жостаточно 2 монеты переварачиваем")
                    amount1_ = balance_2
                    amount0_ = self.check_amount0(pool_tick, tick_low, tick_high, int(amount1_))
                elif auto_amount and balance_1 < int(amount0_):
                    inv_log().info("не жостаточно 1, ставим сколько имеется")
                    amount0_ = balance_1
                else:
                    raise "Минт крашнулся"
            tx = contract.functions.mint(
                (
                    self.pool_token[name_pools][0][0],
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
                    )).build_transaction(
                {
                    'from': wallet,
                    'nonce': self.web3.eth.get_transaction_count(wallet),
                    'chainId': self.web3.eth.chain_id,
                    'gasPrice': self.web3.eth.gas_price,
                    'gas': 0
                }
            )

            name = name_pools.split("-")
            module_str = (f'Mint NFT | {pool_tick[1]} / {tick_low} / {tick_high} | {round(amount0_ / 10 ** decimal1, 5)} '
                          f'{name[0]} | {round(amount1_ / 10 **  decimal2, 5)} {name[1]}')
            tx_bool = EVM.sending_tx(self.web3, tx, self.chain[name_pools], private_key, 1, module_str)
            if not tx_bool:
                log().error('Зафейлилась транза')
                time.sleep(15)
                if retry <= 5:
                    return self.mint(retry + 1)
                else:
                    raise 'Не получается заминтить НФТ'

            else:
                time.sleep(15)
                if self.check_id_nft():
                    return pool_tick[1]
                else:
                    log().error("Минт не проше́л пробуем ещ́ё раз")
                    return self.mint()
        except BaseException as error:
            log().error(error)
            time.sleep(10)
            if retry <= 5:
                return self.mint(retry + 1)
            else:
                raise 'Не вышло'

    def check_balance(self, tick_low, tick_high, wallet, tick_spacing, amount0_):
        _, amount2_ = self.create_tx_V4(tick_low, tick_high, wallet, 'TOKEN_0', tick_spacing,
                                        int(amount0_ / 10))
        balance_2, _ = EVM.check_balance(private_key, 'uni', self.uni_V4[name_pools][1])
        if balance_2 / 10 >= int(amount2_):
            return 'TOKEN_0'
        else:
            return 'TOKEN_1'

    def mint_V4(self, retry=0):
        try:
            if 'ETH' not in name_pools:
                balance_1, decimal1 = EVM.check_balance(private_key, 'uni', self.uni_V4[name_pools][0])
            else:
                balance_1, decimal1 = EVM.check_balance(private_key, 'uni', '')
            amount0_ = int(amount0 * 10 ** decimal1)
            web3, contract = contract_withdrawal('nft_uni')
            wallet = web3.eth.account.from_key(private_key).address
            pool_tick, tick_spacing = self.check_ticket_V4()
            tick_high, tick_low = self.calculation_tick_V4(pool_tick, tick_spacing)
            for i in range(2):
                if self.uni_V4[name_pools][i] != '0x0000000000000000000000000000000000000000':
                    EVM.approve(amount0_, private_key, 'uni', self.uni_V4[name_pools][i],
                                '0x000000000022D473030F116dDEE9F6B43aC78BA3')

            independent_token = self.check_balance(tick_low, tick_high, wallet, tick_spacing, amount0_)
            if independent_token == 'TOKEN_0':
                amount_out = amount0_
            else:
                amount_out, _ = EVM.check_balance(private_key, 'uni', self.uni_V4[name_pools][1])
                amount_out = int(amount_out * 0.99)

            data, amount1_ = self.create_tx_V4(tick_low, tick_high, wallet, independent_token, tick_spacing, amount_out)

            tx = {'from': wallet, 'nonce': web3.eth.get_transaction_count(wallet), 'chainId': web3.eth.chain_id,
                  'gasPrice': web3.eth.gas_price, 'gas': 0, 'to': Web3.to_checksum_address(data['to']),
                  'value': int(data['value'], 16), 'data': data['data']}

            name = name_pools.split("-")

            _, decimal2 = EVM.check_balance(private_key, 'uni', self.uni_V4[name_pools][1])
            print_amount1 = amount_out if independent_token == 'TOKEN_0' else amount1_
            print_amount2 = amount_out if independent_token == 'TOKEN_1' else amount1_
            module_str = (f'Mint NFT | {pool_tick} / {tick_low} / {tick_high} | {round(int(print_amount1) / 10 ** decimal1, 5)} '
                          f'{name[0]} | {round(int(print_amount2) / 10 **  decimal2, 5)} {name[1]}')
            tx_bool = EVM.sending_tx(web3, tx, 'uni', private_key, 1, module_str)
            if not tx_bool:
                log().error('Зафейлилась транза')
                time.sleep(15)
                if retry <= 5:
                    return self.mint_V4(retry + 1)
                else:
                    raise 'Не получается заминтить НФТ'

            else:
                time.sleep(15)
                id_ = self.check_id_V4()
                if id_:
                    return id_
                else:
                    log().error("Минт не проше́л пробуем ещ́ё раз")
                    return self.mint_V4()
        except BaseException as error:
            log().error(error)
            time.sleep(10)
            if retry <= 5:
                return self.mint_V4(retry + 1)
            else:
                raise 'Не вышло'

    def create_tx_V4(self, tick_low, tick_high, address, independentToken, tickSpacing, amount):
        try:
            json_data = {
                'simulateTransaction': False,
                'protocol': 'V4',
                'walletAddress': address,
                'chainId': 130,
                'independentAmount': str(amount),
                # 'slippageTolerance': 0,
                'independentToken': independentToken,  # TOKEN_0, TOKEN_1
                'position': {
                    'tickLower': tick_low,
                    'tickUpper': tick_high,
                    'pool': {
                        'tickSpacing': tickSpacing,
                        'token0': self.uni_V4[name_pools][0],
                        'token1': self.uni_V4[name_pools][1],
                        'fee': self.fee_pool[name_pools],
                    },
                },
            }

            response = self.session.post('https://trading-api-labs.interface.gateway.uniswap.org/v1/lp/create',
                                         json=json_data)
            return response.json()['create'], response.json()['dependentAmount']
        except BaseException as error:
            log().error(error)
            time.sleep(20)
            return self.create_tx_V4(tick_low, tick_high, address, independentToken, tickSpacing, amount)

    def decrease_liquidity(self, token_id, tick_low, tick_high, tick_spacing, retry=0):
        try:
            web3 , contract = contract_withdrawal('nft_uni')
            positionLiquidity = contract.functions.getPositionLiquidity(token_id).call()
            wallet = web3.eth.account.from_key(private_key).address

            json_data = {
                'simulateTransaction': True,
                'protocol': 'V4',
                'tokenId': token_id,
                'chainId': 130,
                'walletAddress': wallet,
                'liquidityPercentageToDecrease': 100,
                'positionLiquidity': str(positionLiquidity),
                'position': {
                    'tickLower': tick_low,
                    'tickUpper': tick_high,
                    'pool': {
                        'token0': self.uni_V4[name_pools][0],
                        'token1': self.uni_V4[name_pools][1],
                        'fee': self.fee_pool[name_pools],
                        'tickSpacing': tick_spacing,
                        'hooks': '0x0000000000000000000000000000000000000000',
                    },
                },
            }

            response = self.session.post(
                'https://trading-api-labs.interface.gateway.uniswap.org/v1/lp/decrease', json=json_data,
            )
            data = response.json()['decrease']

            tx = {'from': wallet, 'nonce': web3.eth.get_transaction_count(wallet), 'chainId': web3.eth.chain_id,
                  'gasPrice': web3.eth.gas_price, 'gas': 0, 'to': Web3.to_checksum_address(data['to']),
                  'data': data['data']}
            module_str = 'Withdraw liquidity, claim rewards, and burn the NFT'
            tx_bool = EVM.sending_tx(web3, tx, 'uni', private_key, 1, module_str)
            if not tx_bool:
                time.sleep(5)
                log().error('Filed tx')
                if retry <= 3:
                    return self.decrease_liquidity(token_id, tick_low, tick_high, tick_spacing, retry + 1)
                raise "Couldn't withdraw liquidity"
            else:
                return True

        except BaseException as error:
            log().error(error)
            if retry <= 5:
                time.sleep(15)
                return self.decrease_liquidity(token_id, tick_low, tick_high, tick_spacing, retry+1)
            else:
                raise "Не прошло"

    def check_ticket_V4(self, retry=0):
        try:
            json_data = {
                'chainId': 130,
                'token0': self.uni_V4[name_pools][0],
                'token1': self.uni_V4[name_pools][1],
                'protocolVersions': [
                    'PROTOCOL_VERSION_V4',
                ],
                'fee': self.fee_pool[name_pools],
                'hooks': '0x0000000000000000000000000000000000000000',
            }

            response = self.session.post(
                'https://interface.gateway.uniswap.org/v2/pools.v1.PoolsService/ListPools', json=json_data,
            )
            data = response.json()['pools'][0]
            return data['tick'], data['tickSpacing']
        except BaseException as error:
            log().error(error)
            time.sleep(10)
            if retry <= 10:
                return self.check_ticket_V4()
            else:
                raise 'Ошибка при получении тикета'

    def get_position_V4(self):
        json_data = {
            'address': self.wallet,
            'chainIds': [
                130,
            ],
            'protocolVersions': [
                'PROTOCOL_VERSION_V4',
                'PROTOCOL_VERSION_V3',
                'PROTOCOL_VERSION_V2',
            ],
            'positionStatuses': [
                'POSITION_STATUS_IN_RANGE',
                'POSITION_STATUS_OUT_OF_RANGE',
            ],
            'pageSize': 100,
            'pageToken': '',
            'includeHidden': True,
        }

        response = self.session.post(
            'https://interface.gateway.uniswap.org/v2/pools.v1.PoolsService/ListPositions', json=json_data,
        )
        data = response.json()['positions']
        if data.get('v4Position'):
            return data['v4Position']['poolPosition']

    def test_withdraw(self, id_nft, retry=0):
        try:
            while not id_nft:
                if not id_nft:
                    id_nft = self.check_id_nft()
                    log().error(f"Не передали NFT id ищем.... --- {id_nft}")
                time.sleep(10)
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
            tx_bool = EVM.sending_tx(web3, tx, self.chain[name_pools], private_key, 1, module_str)
            if not tx_bool:
                time.sleep(5)
                log().error('Filed tx')
                if retry <= 3:
                    return self.test_withdraw(id_nft, retry + 1)
                raise "Couldn't withdraw liquidity"
            else:
                time.sleep(5)
                id_ = self.check_id_nft()
                if id_:
                    if id_ == id_nft:
                        return self.test_withdraw(id_nft)
                return True
        except BaseException as error:
            log().error(error)
            if retry <= 5:
                time.sleep(15)
                return self.test_withdraw(id_nft)
            else:
                raise "Не прошло"

    def burn_nft(self, id_nft, retry=0):
        web3, contract = contract_withdrawal('nft_uni')
        wallet = web3.eth.account.from_key(private_key).address
        tx = contract.functions.burn(id_nft).build_transaction({
            'from': wallet,
            'nonce': web3.eth.get_transaction_count(wallet),
            'chainId': web3.eth.chain_id,
            'gasPrice': web3.eth.gas_price,
            'gas': 0
        })
        module_str = 'Burn the NFT'
        tx_bool = EVM.sending_tx(web3, tx, self.chain[name_pools], private_key, 1, module_str)
        if not tx_bool:
            time.sleep(5)
            log().error('Зафейлилась транза')
            if retry <= 3:
                return self.burn_nft(id_nft, retry + 1)
            raise 'НЕ смолги стереть нфт'
        else:

            return True
