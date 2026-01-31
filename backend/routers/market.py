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
    """Returns the average price (in Yang) over time for a specific item."""
    from sqlalchemy import func
    
    # Group by date (simplistic approach for SQLite)
    # Note: For production, you'd want more robust date handling based on DB type
    results = db.query(
        func.date(models.Listing.seen_at).label("date"), 
        func.avg(models.Listing.total_price_yang).label("avg_price")
    ).join(models.Item)\
    .filter(models.Item.name == item_name)\
    .group_by(func.date(models.Listing.seen_at))\
    .order_by(func.date(models.Listing.seen_at))\
    .all()
    
    return [{"date": str(row.date), "avg_price": row.avg_price} for row in results]

@router.get("/servers")
def get_servers(db: Session = Depends(database.get_db)):
    return db.query(models.Server).all()
