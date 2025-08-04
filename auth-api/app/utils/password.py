"""
Password hashing and verification utilities.
"""

import secrets
import string

from passlib.context import CryptContext


class PasswordManager:
    """Handles password hashing and verification."""

    def __init__(self):
        # Use bcrypt with automatic salt generation
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12,  # Good balance of security vs performance
        )

    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Stored hash to verify against

        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def needs_update(self, hashed_password: str) -> bool:
        """
        Check if password hash needs updating (e.g., different algorithm or rounds).

        Args:
            hashed_password: Stored hash to check

        Returns:
            True if hash should be updated, False otherwise
        """
        return self.pwd_context.needs_update(hashed_password)


class TokenGenerator:
    """Generates secure random tokens for password reset, email verification, etc."""

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        Generate a cryptographically secure random token.

        Args:
            length: Length of the token

        Returns:
            Secure random token
        """
        # Use URL-safe characters (no special characters that might cause issues in URLs)
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def generate_numeric_token(length: int = 6) -> str:
        """
        Generate a numeric token (useful for email verification codes).

        Args:
            length: Length of the numeric token

        Returns:
            Numeric token
        """
        return "".join(secrets.choice(string.digits) for _ in range(length))


# Global instances
password_manager = PasswordManager()
token_generator = TokenGenerator()


# Convenience functions for easier importing
def hash_password(password: str) -> str:
    """Hash a password."""
    return password_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return password_manager.verify_password(plain_password, hashed_password)


def generate_reset_token() -> str:
    """Generate a password reset token."""
    return token_generator.generate_secure_token(32)


def generate_verification_token() -> str:
    """Generate an email verification token."""
    return token_generator.generate_secure_token(32)
