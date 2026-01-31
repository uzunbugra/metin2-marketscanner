from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ServerBase(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class ItemBase(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    image_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class ListingBonusBase(BaseModel):
    bonus_name: str
    bonus_value: Optional[str] = None
    
    class Config:
        from_attributes = True

class ListingOut(BaseModel):
    id: int
    server: ServerBase
    item: ItemBase
    seller_name: str
    quantity: int
    price_won: int
    price_yang: int
    total_price_yang: int
    seen_at: datetime
    bonuses: List[ListingBonusBase] = [] 

    class Config:
        from_attributes = True
