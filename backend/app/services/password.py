import re
from typing import Tuple
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


class PasswordService:
    """
    Enterprise-grade Password Security Service using the Argon2 hashing algorithm
    to secure credentials against offline GPU cracking and side-channel timing attacks.
    """
    
    def __init__(self) -> None:
        # Standard Argon2 config (safe, memory-hard default tuning parameters)
        self.ph = PasswordHasher(
            time_cost=3,      # number of iterations
            memory_cost=65536, # memory usage in kibibytes
            parallelism=4,     # number of parallel threads
            hash_len=32,       # length of output hash
            salt_len=16        # length of salt
        )

    def hash_password(self, password: str) -> str:
        """
        Derives an Argon2 cryptographically secure salted one-way hash from raw password.
        """
        return self.ph.hash(password)

    def verify_password(self, password_hash: str, password: str) -> bool:
        """
        Safely verifies password against Argon2 hash with timing-attack mitigation.
        """
        try:
            return self.ph.verify(password_hash, password)
        except VerifyMismatchError:
            return False
        except Exception:
            return False

    def needs_rehash(self, password_hash: str) -> bool:
        """
        Identifies if an existing hash requires rehabilitation due to updated security standards.
        """
        return self.ph.check_needs_rehash(password_hash)

    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """
        Enforces defensive password complexity rules:
        - Minimum length of 8 characters
        - At least 1 uppercase alphabetical letter
        - At least 1 lowercase alphabetical letter
        - At least 1 numerical digit
        - At least 1 special character (e.g., @, $, !, %, *, ?, &)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters in length."
        if not re.search(r"[A-Z]", password):
            return False, "Password must include at least one uppercase alphabetical character."
        if not re.search(r"[a-z]", password):
            return False, "Password must include at least one lowercase alphabetical character."
        if not re.search(r"\d", password):
            return False, "Password must include at least one numerical digit."
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must include at least one special character (e.g., !@#$%^&*)."
        
        return True, "Password meets security strength requirements."
