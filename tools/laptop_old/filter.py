from typing import List, Dict, Any
from .search import Laptop

def filter_laptops(
    laptops: List[Laptop],
    user_requirements: Dict[str, Any],
) -> List[Laptop]:
    """
    Filter laptops based on specific user requirements.
    
    Args:
        laptops: List of laptops to filter
        user_requirements: Dictionary of requirements like:
            {
                "min_ram": "8GB",
                "min_storage": "512GB",
                "processor_type": ["Intel", "AMD"],
                "has_dedicated_gpu": True,
            }
    
    Returns:
        Filtered list of Laptop objects
    """
    filtered_laptops = laptops[:]
    
    if not user_requirements:
        return filtered_laptops
        
    # Filter by RAM
    if "min_ram" in user_requirements:
        min_ram = _parse_ram(user_requirements["min_ram"])
        filtered_laptops = [
            l for l in filtered_laptops
            if _parse_ram(l.specs.ram) >= min_ram
        ]
    
    # Filter by storage
    if "min_storage" in user_requirements:
        min_storage = _parse_storage(user_requirements["min_storage"])
        filtered_laptops = [
            l for l in filtered_laptops
            if _parse_storage(l.specs.storage) >= min_storage
        ]
    
    # Filter by processor type
    if "processor_type" in user_requirements:
        allowed_processors = user_requirements["processor_type"]
        filtered_laptops = [
            l for l in filtered_laptops
            if any(p.lower() in l.specs.processor.lower() for p in allowed_processors)
        ]
    
    # Filter by GPU requirement
    if user_requirements.get("has_dedicated_gpu"):
        filtered_laptops = [
            l for l in filtered_laptops
            if not any(x in l.specs.graphics.lower() for x in ["intel", "integrated"])
        ]
    
    return filtered_laptops

def _parse_ram(ram_str: str) -> int:
    """Convert RAM string to GB value."""
    ram_str = ram_str.lower()
    if "gb" not in ram_str:
        return 0
    return int(ram_str.replace("gb", "").strip())

def _parse_storage(storage_str: str) -> int:
    """Convert storage string to GB value."""
    storage_str = storage_str.lower()
    if "tb" in storage_str:
        return int(float(storage_str.replace("tb", "").strip()) * 1024)
    elif "gb" in storage_str:
        return int(storage_str.replace("gb", "").strip())
    return 0 