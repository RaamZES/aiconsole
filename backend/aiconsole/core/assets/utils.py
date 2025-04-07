import uuid

def generate_unique_id(prefix: str = "") -> str:
    """
    Generates a unique ID for an asset.
    
    Args:
        prefix: Optional prefix to add to the ID (e.g., 'agent_' or 'material_')
        
    Returns:
        A unique ID string
    """
    # Generate a UUID and take the first 8 characters
    unique_part = str(uuid.uuid4())[:8]
    
    # Combine with prefix if provided
    if prefix:
        return f"{prefix}{unique_part}"
    else:
        return unique_part 