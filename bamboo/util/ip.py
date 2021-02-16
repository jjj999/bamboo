
LOCALHOST = "localhost"


def is_valid_ipv4(ip: str) -> bool:
    if ip == LOCALHOST:
        return True
    
    locs = ip.split(".")
    if len(locs) != 4:
        return False
    
    try:
        for loc in map(int, locs):
            if not(0 <= loc <= 255):
                return False
    except ValueError:
        return False
    
    return True
