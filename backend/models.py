from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Server(Base):
    __tablename__ = "servers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    category = Column(String)
    image_url = Column(String, nullable=True)

class Listing(Base):
    __tablename__ = "listings"
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    seller_name = Column(String)
    quantity = Column(Integer)
    price_won = Column(Integer, default=0)
    price_yang = Column(Integer, default=0)
    total_price_yang = Column(BigInteger)
    seen_at = Column(DateTime(timezone=True), server_default=func.now())

    server = relationship("Server")
    item = relationship("Item")
    bonuses = relationship("ListingBonus", back_populates="listing")

class ListingBonus(Base):
    __tablename__ = "listing_bonuses"
    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"))
    bonus_name = Column(String)
    bonus_value = Column(String)

    listing = relationship("Listing", back_populates="bonuses")
