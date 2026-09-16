import os
import time
import uuid


def generate_uuidv7() -> uuid.UUID:
    """
    Generates a cryptographically secure UUIDv7 (RFC 9562).
    Structure:
    - 48 bits: Unix timestamp in milliseconds.
    - 4 bits: Version (0111 / 7).
    - 12 bits: High-precision rand / seq.
    - 2 bits: Variant (10 / standard).
    - 62 bits: Cryptographic random bytes.
    Benefits: Ordered in time, highly index-friendly for PostgreSQL primary keys.
    """
    # 48 bits timestamp (Unix epoch in ms)
    unix_ts_ms = int(time.time() * 1000)
    
    # 16-bit high-precision rand / sequence (12 bits used)
    # We acquire 10 random bytes total (80 bits)
    rand_bytes = bytearray(os.urandom(10))
    
    # Assemble UUIDv7 bytes:
    # Byte 0-5: Timestamp
    ts_bytes = unix_ts_ms.to_bytes(6, byteorder="big")
    
    uuid_bytes = bytearray(16)
    uuid_bytes[0:6] = ts_bytes
    uuid_bytes[6:16] = rand_bytes
    
    # Set version bits to 7 (0111 on the most significant 4 bits of byte 6)
    # Clear and set: (val & 0x0F) | 0x70
    uuid_bytes[6] = (uuid_bytes[6] & 0x0F) | 0x70
    
    # Set variant bits to standard (10xx on the most significant 2 bits of byte 8)
    # Clear and set: (val & 0x3F) | 0x80
    uuid_bytes[8] = (uuid_bytes[8] & 0x3F) | 0x80
    
    return uuid.UUID(bytes=bytes(uuid_bytes))


def is_valid_uuid(val: str) -> bool:
    """Checks if a string represents a structurally valid UUID."""
    try:
        uuid.UUID(val)
        return True
    except ValueError:
        return False
