from typing import List, Optional
from pydantic import BaseModel

class Accessory(BaseModel):
    id: str
    name: str
    category: str
    description: str
    price: float
    compatibility: List[str]

def search_accessories(
    price_range: Optional[tuple[float, float]] = None,
    category: Optional[str] = None,
    offset: int = 0,
    limit: int = 5,
) -> List[Accessory]:
    """
    Search for accessories based on given criteria.
    
    Args:
        price_range: Tuple of (min_price, max_price)
        category: Category to filter (e.g., "headphones", "mouse", "keyboard")
        offset: Pagination offset
        limit: Number of results to return
    
    Returns:
        List of matching Accessory objects
    """
    # TODO: Implement actual database query
    # This is a mock implementation
    sample_accessories = [
        Accessory(
            id="1",
            name="Logitech MX Master 3",
            category="mouse",
            description="Premium wireless mouse with advanced features",
            price=2490000,
            compatibility=["Windows", "MacOS", "Linux"],
        ),
        Accessory(
            id="2",
            name="Sony WH-1000XM4",
            category="headphones",
            description="Wireless noise-cancelling headphones",
            price=5990000,
            compatibility=["All devices with Bluetooth"],
        ),
    ]
    
    # Apply filters
    if price_range:
        min_price, max_price = price_range
        sample_accessories = [
            a for a in sample_accessories 
            if min_price <= a.price <= max_price
        ]
    
    if category:
        sample_accessories = [
            a for a in sample_accessories 
            if a.category.lower() == category.lower()
        ]
    
    # Apply pagination
    return sample_accessories[offset:offset + limit] 