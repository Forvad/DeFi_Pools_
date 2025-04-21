from web3 import Web3

from Abi.abi import open_abi
from Utils.EVMutils import EVM
from config import name_pools

pool_nft = {'ETH-USDC': '0xF33a96b5932D9E9B9A0eDA447AbD8C9d48d2e0c8',
            'ETH-cbBTC': '0x41b2126661C673C2beDd208cC72E85DC51a5320a',
            'VIRTUAL-ETH': '0x5013Ea8783Bfeaa8c4850a54eacd54D7A3B7f889',
            'USDC-cbBTC': '0x6399ed6725cC163D019aA64FF55b22149D7179A8'
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
    elif name == 'USDC-cbBTC':
        return web3, web3.eth.contract(
            address=Web3.to_checksum_address('0x4e962bb3889bf030368f56810a9c96b83cb3e778'), abi=open_abi()['ETH-USD'])
    elif name == 'check_amount1':
        return web3, web3.eth.contract(
            address=Web3.to_checksum_address('0x0AD09A66af0154a84e86F761313d02d0abB6edd5'), abi=open_abi()['chek_pool'])
    elif name == 'nft':
        return web3, web3.eth.contract(
            address=Web3.to_checksum_address('0x827922686190790b37229fd06084350E74485b72'), abi=open_abi()['nft'])
    elif name == 'pool_nft':
        return web3, web3.eth.contract(
            address=Web3.to_checksum_address(pool_nft[name_pool]), abi=open_abi()['pool_nft'])
    elif name == 'nft_uni':
        if name_pools == 'ETH-USDC-base':
            return web3, web3.eth.contract(
                address=Web3.to_checksum_address('0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1'),
                abi=open_abi()['uni_abi'])
        elif name_pools == 'ETH-USDC-arb':
            web3 = EVM.web3('arbitrum')
            return web3, web3.eth.contract(
                address=Web3.to_checksum_address('0xC36442b4a4522E871399CD717aBDD847Ab11FE88'),
                abi=open_abi()['uni_abi'])
        elif name_pools == 'ETH-USDC-eth':
            web3 = EVM.web3('ethereum')
            return web3, web3.eth.contract(
                address=Web3.to_checksum_address('0xC36442b4a4522E871399CD717aBDD847Ab11FE88slava6680'),
                abi=open_abi()['uni_abi'])
        elif 'uni' in name_pools:
            web3 = EVM.web3('uni')
            return web3, web3.eth.contract(
                address=Web3.to_checksum_address('0x4529A01c7A0410167c5740C487A8DE60232617bf'),
                abi=open_abi()['uni_V4'])
    else:
        return None
