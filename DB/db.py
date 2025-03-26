import logging

from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker


Base = declarative_base()


class NFT(Base):
    __tablename__ = 'nfts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nft_id = Column(Integer, unique=True, nullable=False)
    initial_tick = Column(Integer, nullable=False)
    high_tick = Column(Integer, nullable=False)
    low_tick = Column(Integer, nullable=False)
    replay = Column(Boolean, nullable=False)


class NFTDatabase:
    def __init__(self, db_url='sqlite:///nft.db'):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_nft(self, nft_id, initial_tick, high_tick, low_tick, replay=False):
        session = self.Session()
        existing_nft = session.query(NFT).filter_by(nft_id=nft_id).first()
        if existing_nft:
            session.close()
            return

        new_nft = NFT(nft_id=nft_id, initial_tick=initial_tick, high_tick=high_tick, low_tick=low_tick, replay=replay)
        session.add(new_nft)
        session.commit()
        session.close()

    def get_nft_by_id(self, nft_id) -> NFT:
        session = self.Session()
        nft = session.query(NFT).filter_by(nft_id=nft_id).first()
        session.close()
        if nft:
            return nft
        else:
            return None

    def update_nft(self, nft_id, high_tick=None, low_tick=None, replay=None):
        session = self.Session()
        nft = session.query(NFT).filter_by(nft_id=nft_id).first()
        if not nft:
            session.close()
            return

        if high_tick is not None:
            nft.high_tick = high_tick
        if low_tick is not None:
            nft.low_tick = low_tick
        if replay is not None:
            nft.replay = replay

        session.commit()
        session.close()


# Пример использования класса
if __name__ == "__main__":
    db = NFTDatabase()

    # Добавление нового NFT
    db.add_nft('1234566', 100, 110, 90)

    # Поиск NFT по id
    nft = db.get_nft_by_id('1234566')
    if nft:
        print(f"Найден NFT: id={nft.nft_id}, initial_tick={nft.initial_tick}, high_tick={nft.high_tick}, low={nft.low_tick}")



