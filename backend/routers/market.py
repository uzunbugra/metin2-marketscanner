from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas, database

router = APIRouter(
    prefix="/market",
    tags=["market"]
)

@router.get("/listings", response_model=List[schemas.ListingOut])
def get_listings(
    skip: int = 0, 
    limit: int = 100, 
    server: Optional[str] = None, 
    item_name: Optional[str] = None,
    sort_by: Optional[str] = "newest",
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Listing)
    
    if server:
        query = query.join(models.Server).filter(models.Server.name == server)
    if item_name:
        query = query.join(models.Item).filter(models.Item.name.contains(item_name))
        
    if sort_by == "newest":
        query = query.order_by(models.Listing.seen_at.desc())
    elif sort_by == "price_asc":
        query = query.order_by(models.Listing.total_price_yang.asc())
    elif sort_by == "price_desc":
        query = query.order_by(models.Listing.total_price_yang.desc())

    listings = query.offset(skip).limit(limit).all()
    return listings

@router.get("/stats/top-items")
def get_top_items(db: Session = Depends(database.get_db)):
    """Returns the most frequently listed items (by listing count)."""
    from sqlalchemy import func
    results = db.query(models.Item.name, func.count(models.Listing.id).label("count")) \
        .join(models.Listing) \
        .group_by(models.Item.name) \
        .order_by(func.count(models.Listing.id).desc()) \
        .limit(10).all()
    
    return [{"name": name, "count": count} for name, count in results]

@router.get("/stats/price-history")
def get_price_history(item_name: str, db: Session = Depends(database.get_db)):
    """Returns the recorded price history for a specific item."""
    history = db.query(models.PriceHistory)\
        .filter(models.PriceHistory.item_name == item_name)\
        .order_by(models.PriceHistory.timestamp.asc())\
        .all()
    
    return [
        {
            "timestamp": h.timestamp, 
            "avg_unit_price": h.avg_unit_price, 
            "min_unit_price": h.min_unit_price,
            "total_listings": h.total_listings
        } 
        for h in history
    ]

@router.get("/servers")
def get_servers(db: Session = Depends(database.get_db)):
    return db.query(models.Server).all()
