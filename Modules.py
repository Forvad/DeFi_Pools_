import time

from config import amount0, private_key, name_pools
from main import mint, check_id_nft, approve_NFT, deposit_withdraw_nft, auto_, clear_nft


def mint_dep():
    mint(amount0, private_key, name_pools, check_amount=True)
    nft_id_ = check_id_nft(private_key)
    if nft_id_:
        time.sleep(2)
        deposit_withdraw_nft(nft_id_, private_key, name_pools)


def withdraw():
    clear_nft(private_key, name_pools)


def approval():
    approve_NFT(private_key, name_pools)


def main():
    print(''' 
                        1) Mint + approve + deposit
                        
                        ----
                        
                        2) withdraw + decreaseLiquidity + burn_nft
                        
                        ---
                        
                        3) Auto
                        
                        ---
                        
                        4) Approve the NFT
    ''')
    modul = int(input('Какой модуль крутим: '))

    modules = {1: mint_dep,
               2: withdraw,
               3: auto_,
               4: approval,
               }
    func = modules[modul]
    func()


if __name__ == '__main__':
    main()