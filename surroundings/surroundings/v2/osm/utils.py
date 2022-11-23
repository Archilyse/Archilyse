def is_tunnel(properties: dict) -> bool:
    """
    metadata for osm railways provide a property whether the railway segment is a tunnel or not
    """
    return properties.get("tunnel") == "T"
