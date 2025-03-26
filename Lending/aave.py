import time

from web3 import Web3

from Abi.abi import open_abi
from Log.Loging import log
from Utils.EVMutils import EVM
from config import private_key


class AAVE:
    def __init__(self, private_key_):
        self.private_key = private_key_
        self.tokens = {'USDC': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
                       'WETH': '0x4200000000000000000000000000000000000006'}
        self.address_contract = '0xA238Dd80C259a72e81d7e4664a9801593F98d1c5'
        self.web3 = EVM.web3('base')
        self.wallet = self.web3.eth.account.from_key(self.private_key).address
        self.contract_pool = self.web3.eth.contract(address=Web3.to_checksum_address(self.address_contract),
                                          abi=open_abi()['aave_abi'])

    def func_contract(self, amount, token, mode, retry=0):
        EVM.approve(amount, self.private_key, 'base', self.tokens[token], self.address_contract)
        if mode in ['repay', 'withdraw']:
            amount = 115792089237316195423570985008687907853269984665640564039457584007913129639935
        if mode == 'supply':
            tx = self.contract_pool.functions.supply(self.tokens[token], amount, self.wallet, 0)
            text = 'Supply'
        elif mode == 'borrow':
            tx = self.contract_pool.functions.borrow(self.tokens[token], amount, 2, 0, self.wallet)
            text = 'Borrow'
        elif mode == 'withdraw':
            tx = self.contract_pool.functions.withdraw(self.tokens[token], amount, self.wallet)
            text = 'Withdraw'
        elif mode == 'repay':
            tx = self.contract_pool.functions.repay(self.tokens[token], amount, 2, self.wallet)
            text = 'Repay'
        else:
            raise 'Choose the right module'

        tx = tx.build_transaction({
            'from': self.wallet,
            'nonce': self.web3.eth.get_transaction_count(self.wallet),
            'chainId': self.web3.eth.chain_id,
            'gasPrice': self.web3.eth.gas_price,
            'gas': 0
        })
        module_str = f'{text} | {token} | {"~~~~~~~" if mode in ["repay", "withdraw"] else amount}'
        tx_bool = EVM.sending_tx(self.web3, tx, 'base', private_key, 1, module_str)
        if not tx_bool:
            log().error('The transaction failed')
            time.sleep(15)
            if retry <= 5:
                return self.func_contract(amount, token, mode, retry + 1)
            else:
                raise "I can't deposit or withdraw"

        else:
            return True

    def user_data(self):
        data = self.contract_pool.functions.getUserAccountData(self.wallet).call()
        return data


if __name__ == '__main__':
    aave = AAVE(private_key)
    aave.func_contract(int(1 * 10 ** 6), 'WETH', 'withdraw')
    # data = aave.user_data()
    # print(round(data[0] / 10 ** 8, 2))
