import time

from config import amount0, private_key, name_pools, nft_id
from main import mint, check_id_nft, approve_NFT, deposit_withdraw_nft, decreaseLiquidity, burn_nft, auto_


def mint_dep():
    mint(amount0, private_key, name_pools)
    # nft_id_ = check_id_nft(private_key)
    # if nft_id_:
    #     time.sleep(2)
    #     approve_NFT(private_key, name_pools)
    #     time.sleep(2)
    #     deposit_withdraw_nft(nft_id_, private_key, name_pools)


def withdraw():
    deposit_withdraw_nft(nft_id, private_key, name_pools, True)
    time.sleep(2)
    decreaseLiquidity(nft_id, private_key, name_pools)
    time.sleep(1)
    burn_nft(nft_id, private_key, name_pools)


def main():
    print(''' 
                        1) Mint + approve + deposit
                        
                        ----
                        
                        2) withdraw + decreaseLiquidity + burn_nft
                        
                        ---
                        
                        3) Auto
    ''')
    modul = int(input('Какой модуль крутим: '))

    modules = {1: mint_dep,
               2: withdraw,
               3: auto_,
               }
    func = modules[modul]
    func()


if __name__ == '__main__':
    main()