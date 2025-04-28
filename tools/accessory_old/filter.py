from typing import List, Dict, Any
from .search import Accessory

def filter_accessories(
    accessories: List[Accessory],
    user_requirements: Dict[str, Any],
) -> List[Accessory]:
    """
    Filter accessories based on specific user requirements.
    
    Args:
        accessories: List of accessories to filter
        user_requirements: Dictionary of requirements like:
            {
                "compatibility": ["Windows", "MacOS"],
                "category": "mouse",
                "wireless": True,
            }
    
    Returns:
        Filtered list of Accessory objects
    """
    filtered_accessories = accessories[:]
    
    if not user_requirements:
        return filtered_accessories
        
    # Filter by compatibility
    if "compatibility" in user_requirements:
        required_compatibility = user_requirements["compatibility"]
        filtered_accessories = [
            a for a in filtered_accessories
            if any(c.lower() in [x.lower() for x in a.compatibility] 
                  for c in required_compatibility)
        ]
    
    # Filter by category
    if "category" in user_requirements:
        category = user_requirements["category"].lower()
        filtered_accessories = [
            a for a in filtered_accessories
            if a.category.lower() == category
        ]
    
    # Filter by wireless requirement
    if user_requirements.get("wireless"):
        filtered_accessories = [
            a for a in filtered_accessories
            if "wireless" in a.description.lower()
        ]
    
    return filtered_accessories 