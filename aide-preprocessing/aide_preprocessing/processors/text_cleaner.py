"""HTML tag removal and text cleaning"""


class TextCleaner:
    """Clean HTML tags and entities from text

    Removes:
    - HTML tags (<b>, </b>, etc.)
    - HTML entities (&quot;, &amp;, etc.)
    """

    @staticmethod
    def clean(text: str) -> str:
        """Remove HTML tags and entities from text

        Args:
            text: Raw text with HTML tags

        Returns:
            Cleaned text

        Example:
            >>> TextCleaner.clean("<b>PF</b> 대출 &quot;위기&quot;")
            'PF 대출 "위기"'
        """
        if not text:
            return ""

        # Remove HTML tags
        text = text.replace('<b>', '').replace('</b>', '')
        text = text.replace('<strong>', '').replace('</strong>', '')
        text = text.replace('<em>', '').replace('</em>', '')
        text = text.replace('<i>', '').replace('</i>', '')
        text = text.replace('<u>', '').replace('</u>', '')

        # Replace HTML entities
        text = text.replace('&quot;', '"')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&#39;', "'")
        text = text.replace('&#x27;', "'")

        return text.strip()

    @staticmethod
    def clean_title(title: str) -> str:
        """Clean title text

        Args:
            title: Raw title

        Returns:
            Cleaned title
        """
        return TextCleaner.clean(title)

    @staticmethod
    def clean_description(description: str) -> str:
        """Clean description text

        Args:
            description: Raw description

        Returns:
            Cleaned description
        """
        return TextCleaner.clean(description)
