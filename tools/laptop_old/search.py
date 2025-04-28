from typing import List, Optional
from pydantic import BaseModel

class LaptopSpecs(BaseModel):
    processor: str
    ram: str
    storage: str
    display: str
    graphics: str

class Laptop(BaseModel):
    id: str
    name: str
    brand: str
    price: float
    specs: LaptopSpecs
    specs_summary: str

def search_laptops(
    price_range: Optional[tuple[float, float]] = None,
    brand: Optional[str] = None,
    offset: int = 0,
    limit: int = 5,
) -> List[Laptop]:
    """
    Search for laptops based on given criteria.
    
    Args:
        price_range: Tuple of (min_price, max_price)
        brand: Brand name to filter
        offset: Pagination offset
        limit: Number of results to return
    
    Returns:
        List of matching Laptop objects
    """
    # TODO: Implement actual database query
    # This is a mock implementation
    sample_laptops = [
        Laptop(
            id="1",
            name="Dell XPS 13",
            brand="Dell",
            price=25990000,
            specs=LaptopSpecs(
                processor="Intel Core i7-1165G7",
                ram="16GB DDR4",
                storage="512GB SSD",
                display="13.3 inch 4K",
                graphics="Intel Iris Xe",
            ),
            specs_summary="Core i7, 16GB RAM, 512GB SSD",
        ),
        Laptop(
            id="2",
            name="MacBook Air M1",
            brand="Apple",
            price=24990000,
            specs=LaptopSpecs(
                processor="Apple M1",
                ram="8GB",
                storage="256GB SSD",
                display="13.3 inch Retina",
                graphics="M1 7-core GPU",
            ),
            specs_summary="M1, 8GB RAM, 256GB SSD",
        ),
    ]
    
    # Apply filters
    if price_range:
        min_price, max_price = price_range
        sample_laptops = [
            l for l in sample_laptops 
            if min_price <= l.price <= max_price
        ]
    
    if brand:
        sample_laptops = [
            l for l in sample_laptops 
            if l.brand.lower() == brand.lower()
        ]
    
    # Apply pagination
    return sample_laptops[offset:offset + limit] 