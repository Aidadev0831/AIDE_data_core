"""Generate content hash for deduplication"""

import hashlib


class HashGenerator:
    """Generate SHA-256 hash from content

    Used for deduplication by creating a unique hash
    from title + description.
    """

    @staticmethod
    def generate(title: str, description: str = "") -> str:
        """Generate SHA-256 hash from title and description

        Args:
            title: Article title
            description: Article description (optional)

        Returns:
            SHA-256 hash (hex string)

        Example:
            >>> HashGenerator.generate("PF 대출 위기", "프로젝트 파이낸싱...")
            'a1b2c3d4e5f6...'
        """
        content = f"{title}{description}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
