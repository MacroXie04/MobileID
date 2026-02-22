import base64


def _clean_base64(b64: str) -> str:
    """
    Remove any data-URI prefix and return the raw Base64.
    """
    if b64.startswith("data:image"):
        b64 = b64.split(",", 1)[1]
    return b64.strip()


def _b64_any_to_bytes(data: str) -> bytes:
    """
    Decode Base64 in a robust way:
    - Accept both standard and URL-safe Base64
    - Auto-fix missing padding
    """
    if not isinstance(data, str):
        raise ValueError("Invalid base64 data")
    s = data.strip().replace("-", "+").replace("_", "/")
    # Add padding to multiple of 4
    pad = (-len(s)) % 4
    if pad:
        s += "=" * pad
    return base64.b64decode(s)
