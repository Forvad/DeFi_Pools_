from json import load
from pathlib import Path
from os import listdir
from os.path import isfile, join


def open_abi(mode='') -> {str: str}:
    try:
        mypath = Path('../aerodrome/Abi/')
        list_files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        abi_ = {}
        for file in list_files:
            if 'json' in file:
                with open(mode + file, "r") as f:
                    abi_all = load(f)
                    abi_[file.replace('.json', '').replace('./Abi/', '')] = abi_all
        return abi_
    except FileNotFoundError:
        return open_abi(mode='./Abi/')


ABI = open_abi()
