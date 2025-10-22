"""AI Classification Service - Claude API-based article classification

Classifies news articles into predefined categories using Claude API.

Categories:
1. 정책/규제 (Policy/Regulation)
2. 시장동향 (Market Trends)
3. 금융/투자 (Finance/Investment)
4. 부동산개발 (Real Estate Development)
5. 기업/프로젝트 (Corporate/Projects)
6. 법률/소송 (Legal/Litigation)
7. 경제지표 (Economic Indicators)
8. 기타 (Others)
"""

from typing import Dict, List, Optional
import json
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)


CLASSIFICATION_PROMPT = """다음 부동산/금융 뉴스 기사를 분석하여 카테고리를 분류하고 태그를 추출해주세요.

**기사 정보:**
제목: {title}
내용: {description}

**카테고리 목록:**
1. 정책/규제 - 정부 정책, 규제 변화, 법률 개정
2. 시장동향 - 시장 트렌드, 거래량, 가격 동향
3. 금융/투자 - 금리, 투자, 펀드, 대출
4. 부동산개발 - 개발 프로젝트, 재개발, 신규 공급
5. 기업/프로젝트 - 기업 뉴스, PF, 프로젝트 진행상황
6. 법률/소송 - 법적 분쟁, 소송, 규제 위반
7. 경제지표 - GDP, 물가, 경제 통계
8. 기타 - 위 카테고리에 해당하지 않는 경우

**응답 형식 (JSON):**
{{
  "categories": ["카테고리1", "카테고리2"],
  "tags": ["태그1", "태그2", "태그3"],
  "confidence": 95,
  "reasoning": "분류 근거 설명"
}}

**주의사항:**
- categories는 1~2개만 선택 (가장 관련성 높은 것)
- tags는 핵심 키워드 3~5개 추출
- confidence는 0~100 점수
- reasoning은 한 문장으로 간결하게

JSON만 응답하세요:"""


class ClassificationService:
    """Claude AI Classification Service

    Classifies articles into categories and extracts tags using Claude API.

    Example:
        >>> service = ClassificationService(api_key="your_api_key")
        >>> result = service.classify(
        ...     title="PF 시장 안정화 정책 발표",
        ...     description="정부가 PF 시장 안정화를 위한 정책을 발표..."
        ... )
        >>> print(result)
        {
            "categories": ["정책/규제", "금융/투자"],
            "tags": ["PF", "정책", "안정화"],
            "confidence": 95
        }
    """

    VALID_CATEGORIES = [
        "정책/규제",
        "시장동향",
        "금융/투자",
        "부동산개발",
        "기업/프로젝트",
        "법률/소송",
        "경제지표",
        "기타"
    ]

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 1000,
        temperature: float = 0.0
    ):
        """Initialize classification service

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            max_tokens: Maximum tokens for response
            temperature: Temperature for generation (0 = deterministic)
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        logger.info(f"ClassificationService initialized (model={model})")

    def classify(
        self,
        title: str,
        description: str = ""
    ) -> Dict:
        """Classify article into categories

        Args:
            title: Article title
            description: Article description/content

        Returns:
            Dictionary with:
            - categories: List of category names
            - tags: List of extracted tags
            - confidence: Confidence score (0-100)
        """
        # Prepare prompt
        prompt = CLASSIFICATION_PROMPT.format(
            title=title,
            description=description or title
        )

        try:
            # Call Claude API
            logger.debug(f"Classifying article: {title[:50]}...")
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            response_text = message.content[0].text
            logger.debug(f"Claude response: {response_text[:200]}...")

            # Extract JSON from response
            result = self._parse_response(response_text)

            # Validate categories
            result['categories'] = [
                cat for cat in result.get('categories', [])
                if cat in self.VALID_CATEGORIES
            ]

            # Fallback to "기타" if no valid categories
            if not result['categories']:
                result['categories'] = ["기타"]
                result['confidence'] = min(result.get('confidence', 50), 50)

            logger.info(
                f"Classified: {result['categories']}, "
                f"tags={result.get('tags', [])}, "
                f"confidence={result.get('confidence', 0)}"
            )

            return result

        except Exception as e:
            logger.error(f"Classification failed: {str(e)}")
            return {
                "categories": ["기타"],
                "tags": [],
                "confidence": 0,
                "error": str(e)
            }

    def classify_batch(
        self,
        articles: List[Dict],
        show_progress: bool = True
    ) -> List[Dict]:
        """Classify multiple articles

        Args:
            articles: List of article dictionaries with 'title' and 'description'
            show_progress: Show progress messages

        Returns:
            List of classification results
        """
        results = []
        total = len(articles)

        for i, article in enumerate(articles):
            if show_progress and i % 10 == 0:
                logger.info(f"Classifying {i+1}/{total} articles...")

            result = self.classify(
                title=article.get('title', ''),
                description=article.get('description', '')
            )
            results.append(result)

        logger.info(f"Classified {len(results)} articles")
        return results

    def _parse_response(self, response_text: str) -> Dict:
        """Parse Claude response to extract JSON

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed dictionary
        """
        try:
            # Try to parse as JSON directly
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                return json.loads(json_str)
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                return json.loads(json_str)
            else:
                # Try to extract JSON object directly
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = response_text[start:end]
                    return json.loads(json_str)
                raise ValueError("No valid JSON found in response")

    def validate_categories(self, categories: List[str]) -> List[str]:
        """Validate and filter categories

        Args:
            categories: List of category names

        Returns:
            Filtered list with only valid categories
        """
        return [cat for cat in categories if cat in self.VALID_CATEGORIES]
