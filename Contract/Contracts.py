from web3 import Web3

from Abi.abi import open_abi
from Utils.EVMutils import EVM


pool_nft = {'ETH-USDC': '0xF33a96b5932D9E9B9A0eDA447AbD8C9d48d2e0c8',
            'ETH-cbBTC': '0x41b2126661C673C2beDd208cC72E85DC51a5320a',
            'VIRTUAL-ETH': '0x5013Ea8783Bfeaa8c4850a54eacd54D7A3B7f889'
            }


def contract_withdrawal(name, name_pool=''):
    web3 = EVM.web3('base')
    if name == 'ETH-USDC':
        return web3, web3.eth.contract(
            address=Web3.to_checksum_address('0xb2cc224c1c9feE385f8ad6a55b4d94E92359DC59'), abi=open_abi()['ETH-USD'])
    elif name == 'ETH-cbBTC':
        return web3, web3.eth.contract(
            address=Web3.to_checksum_address('0x70aCDF2Ad0bf2402C957154f944c19Ef4e1cbAE1'), abi=open_abi()['ETH-USD'])
    elif name == 'VIRTUAL-ETH':
        return web3, web3.eth.contract(
            address=Web3.to_checksum_address('3f0296BF652e19bca772EC3dF08b32732F93014A'), abi=open_abi()['ETH-USD'])
    elif name == 'check_amount1':
        return web3, web3.eth.contract(
            address=Web3.to_checksum_address('0x0AD09A66af0154a84e86F761313d02d0abB6edd5'), abi=open_abi()['chek_pool'])
    elif name == 'nft':
        return web3, web3.eth.contract(
            address=Web3.to_checksum_address('0x827922686190790b37229fd06084350E74485b72'), abi=open_abi()['nft'])
    elif name == 'pool_nft':
        return web3, web3.eth.contract(
            address=Web3.to_checksum_address(pool_nft[name_pool]), abi=open_abi()['pool_nft'])
    else:
        return None
