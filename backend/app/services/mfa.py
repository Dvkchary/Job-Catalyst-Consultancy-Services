import secrets
from typing import List
import pyotp


class MFAService:
    """
    Cryptographic Multi-Factor Authentication (MFA) service.
    Implements standard Time-Based One-Time Password (TOTP, RFC 6238)
    and secure backup/recovery code generation.
    """

    @staticmethod
    def generate_totp_secret() -> str:
        """
        Generates a random Base32 TOTP secret key (32 characters).
        """
        return pyotp.random_base32()

    @staticmethod
    def get_totp_provisioning_uri(secret: str, email: str, issuer: str = "JobCatalyst AI") -> str:
        """
        Compiles standard Google Authenticator compatible OTPAuth URI.
        """
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=email.strip(),
            issuer_name=issuer
        )

    @staticmethod
    def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
        """
        Verifies a Time-Based One-Time Password code against a secret key.
        The window parameter permits drift of +/- 30 seconds to ease user experience.
        """
        if not code or not secret:
            return False
        
        totp = pyotp.TOTP(secret)
        # verify returns True if valid, with timing attack safety built-in
        return totp.verify(code.strip(), valid_window=window)

    @staticmethod
    def generate_recovery_codes(count: int = 8) -> List[str]:
        """
        Generates high-entropy backup/recovery codes.
        Formatted as alphanumeric groups (e.g. "ABCD-1234") for human readability.
        """
        codes: List[str] = []
        for _ in range(count):
            # Generate 12 characters of strong random hex
            raw = secrets.token_hex(6).upper()
            formatted = f"{raw[:4]}-{raw[4:8]}-{raw[8:]}"
            codes.append(formatted)
        return codes
