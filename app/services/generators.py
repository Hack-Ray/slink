from typing import Protocol
import secrets
import os
from hashids import Hashids


class ShortCodeGenerator(Protocol):
    """Protocol for short code generation strategies."""

    async def generate(self, original_url: str) -> str:
        """Generates a short code for the given original URL."""
        ...


class HashBasedGenerator:
    """Generates short codes based on a hash of the original URL."""

    async def generate(self, original_url: str) -> str:
        """Generates a short code using Hashids based on URL hash."""
        salt = os.getenv("SECRET_KEY", "your-secret-key-here")
        hashids = Hashids(salt=salt, min_length=6)
        # Using abs(hash()) to ensure a positive integer for encoding
        return hashids.encode(abs(hash(original_url)) % (10**8))


class RandomGenerator:
    """Generates random URL-safe short codes."""

    async def generate(self, original_url: str) -> str:
        """Generates a random URL-safe short code."""
        return secrets.token_urlsafe(6) 