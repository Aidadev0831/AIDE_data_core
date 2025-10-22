"""Extract media source from URL"""


class SourceExtractor:
    """Extract media source name from article URL

    Maps domain patterns to Korean media source names.
    """

    # Domain to source mapping
    SOURCE_MAP = {
        "chosun.com": "조선일보",
        "joongang.co.kr": "중앙일보",
        "donga.com": "동아일보",
        "hankyung.com": "한국경제",
        "mk.co.kr": "매일경제",
        "sedaily.com": "서울경제",
        "hani.co.kr": "한겨레",
        "khan.co.kr": "경향신문",
        "yna.co.kr": "연합뉴스",
        "news1.kr": "뉴스1",
        "newsis.com": "뉴시스",
        "mt.co.kr": "머니투데이",
        "edaily.co.kr": "이데일리",
        "asiae.co.kr": "아시아경제",
        "fnnews.com": "파이낸셜뉴스",
        "etnews.com": "전자신문",
        "dt.co.kr": "디지털타임스",
        "hankookilbo.com": "한국일보",
        "seoul.co.kr": "서울신문",
        "segye.com": "세계일보",
    }

    @staticmethod
    def extract(url: str) -> str:
        """Extract source name from URL

        Args:
            url: Article URL

        Returns:
            Media source name (Korean)

        Example:
            >>> SourceExtractor.extract("https://www.chosun.com/economy/...")
            '조선일보'
        """
        if not url:
            return "기타"

        # Check each domain pattern
        for domain, source in SourceExtractor.SOURCE_MAP.items():
            if domain in url:
                return source

        return "기타"
