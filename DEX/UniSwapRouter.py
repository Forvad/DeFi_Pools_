import time

from web3 import Web3

from Log.Loging import log
from Utils.EVMutils import EVM
from config import private_key
from DeFI.Uniswap import UniSwap


class UniRouter(UniSwap):
    def swap(self, token1, token2, amount, amount_=None):
        try:
            if not amount_:
                amount_ = int(self.quote_create(amount, token2, token1)['input']['amount'])

            quote = self.quote_create(amount_, token1, token2)

            json_data = {

                'quote': quote,
                'simulateTransaction': False,
                'refreshGasPrice': True,
                'gasStrategies': [
                    {
                        'limitInflationFactor': 1.15,
                        'displayLimitInflationFactor': 1,
                        'priceInflationFactor': 1.5,
                        'percentileThresholdFor1559Fee': 75,
                        'thresholdToInflateLastBlockBaseFee': 0,
                        'baseFeeMultiplier': 1.05,
                        'baseFeeHistoryWindow': 100,
                        'minPriorityFeeGwei': 2,
                        'maxPriorityFeeGwei': 20,
                    },
                ],
                'urgency': 'normal',
            }

            response = self.session.post('https://trading-api-labs.interface.gateway.uniswap.org/v1/swap',
                                         json=json_data)

            data_tx = response.json()['swap']
            if token1 != '0x0000000000000000000000000000000000000000':
                EVM.approve(amount, private_key, 'uni', token1, data_tx['to'])
            tx = {
                'value': int(data_tx['value'], 16),
                'data': data_tx['data'],
                'from': Web3.to_checksum_address(data_tx['from']),
                'to': Web3.to_checksum_address(data_tx['to']),
                'chainId': self.web3.eth.chain_id,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': self.web3.eth.get_transaction_count(Web3.to_checksum_address(data_tx['from'])),
                # 'gas': 0
            }
            module_str = f'Swap Token'
            web3 = EVM.web3('uni')
            tx_bool = EVM.sending_tx(web3, tx, 'uni', private_key, 1, module_str)
            if not tx_bool:
                log().error('The transaction failed')
                time.sleep(15)
                return self.swap(token1, token2, amount, amount_)
            else:
                return True
        except BaseException as error:
            log().error(error)
            time.sleep(10)
            return self.swap(token1, token2, amount, amount_)

    def quote_create(self, amount, token1, token2):
        json_data = {
            'amount': str(amount),
            'gasStrategies': [
                {
                    'limitInflationFactor': 1.15,
                    'displayLimitInflationFactor': 1,
                    'priceInflationFactor': 1.5,
                    'percentileThresholdFor1559Fee': 75,
                    'thresholdToInflateLastBlockBaseFee': 0,
                    'baseFeeMultiplier': 1.05,
                    'baseFeeHistoryWindow': 100,
                    'minPriorityFeeGwei': 2,
                    'maxPriorityFeeGwei': 9,
                },
            ],
            'swapper': self.wallet,
            'tokenIn': token1,
            'tokenInChainId': 130,
            'tokenOut': token2,
            'tokenOutChainId': 130,
            'type': 'EXACT_OUTPUT',
            'urgency': 'normal',
            'protocols': [
                'V4',
            ],
        }

        response = self.session.post('https://trading-api-labs.interface.gateway.uniswap.org/v1/quote', json=json_data)
        return response.json()['quote']

