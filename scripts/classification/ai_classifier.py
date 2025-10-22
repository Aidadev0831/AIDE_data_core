#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 기반 뉴스 분류 서비스 (GPT-4o-mini)

- OpenAI GPT-4o-mini 모델 사용
- 배치 처리 (10개씩)
- 멀티라벨 분류 지원
- 태그 자동 추출
- 신뢰도 점수 산출
"""
import os
import json
import time
from typing import List, Dict, Optional
from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 카테고리 정의 (insight_test 기준 9개 카테고리)
CATEGORIES = {
    "policy_regulation": "정책·규제",
    "market_transaction": "시장동향",
    "development_supply": "개발·공급",
    "construction_development": "건설·개발",
    "finance_investment": "금융·투자",
    "commercial_realestate": "상업용부동산",
    "proptech_service": "프롭테크·서비스",
    "auction_public_sale": "경매·공매",
    "overseas_other": "해외·기타"
}

# 카테고리별 설명 (GPT가 이해하기 쉽게)
CATEGORY_DESCRIPTIONS = {
    "policy_regulation": "정부 정책, 법규, 세금, 규제, 제도 변경 등",
    "market_transaction": "매매·전월세 시장 동향, 가격 변동, 거래량 등",
    "development_supply": "택지 개발, 주택 공급, 신도시 계획, 재개발·재건축 등",
    "construction_development": "건설사 동향, 시공, 분양, 입주, 건설 경기 등",
    "finance_investment": "대출, 금리, 투자, 자산관리, 부동산 금융 상품 등",
    "commercial_realestate": "오피스, 리테일, 물류센터 등 상업용 부동산",
    "proptech_service": "프롭테크, 중개 서비스, 플랫폼, 기술 혁신 등",
    "auction_public_sale": "경매, 공매, 법원 경매 시장 등",
    "overseas_other": "해외 부동산, 글로벌 시장, 기타 분류 어려운 기사"
}


class AIClassifier:
    """AI 기반 뉴스 분류기 (GPT-4o-mini)"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: OpenAI API 키 (없으면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"
        self.temperature = 0.3  # 일관성을 위해 낮게 설정

        # Rate limiting
        self.max_requests_per_minute = 50
        self.request_count = 0
        self.last_reset_time = time.time()

    def _check_rate_limit(self):
        """Rate limiting 체크"""
        current_time = time.time()

        # 1분 경과 시 리셋
        if current_time - self.last_reset_time >= 60:
            self.request_count = 0
            self.last_reset_time = current_time

        # 한도 초과 시 대기
        if self.request_count >= self.max_requests_per_minute:
            sleep_time = 60 - (current_time - self.last_reset_time)
            if sleep_time > 0:
                print(f"Rate limit reached, sleeping for {sleep_time:.1f}s...")
                time.sleep(sleep_time)
                self.request_count = 0
                self.last_reset_time = time.time()

        self.request_count += 1

    def _create_classification_prompt(self, articles: List[Dict]) -> str:
        """분류 프롬프트 생성"""

        # 카테고리 설명
        categories_info = "\n".join([
            f"- {code}: {name} ({CATEGORY_DESCRIPTIONS[code]})"
            for code, name in CATEGORIES.items()
        ])

        # 기사 목록
        articles_info = "\n".join([
            f"ID {art['id']}: {art['title']}\n  설명: {art.get('description', 'N/A')}"
            for art in articles
        ])

        prompt = f"""
다음 부동산 뉴스 기사들을 분류해주세요.

## 카테고리 (여러 개 선택 가능)
{categories_info}

## 분류할 기사
{articles_info}

## 요구사항
1. 각 기사마다 1~3개의 가장 적합한 카테고리를 선택하세요
2. 부동산 관련 핵심 태그를 3~5개 추출하세요 (한글만)
3. 분류 신뢰도를 0~100 점수로 매기세요
4. 카테고리 선택 이유를 1문장으로 설명하세요

## 응답 형식 (JSON)
{{
  "classifications": [
    {{
      "id": 1,
      "categories": ["policy_regulation", "finance_investment"],
      "tags": ["대출규제", "DSR", "금리인상", "정책변화", "금융당국"],
      "confidence": 95,
      "reasoning": "정부의 대출 규제 정책과 금융 금리 변화를 다루고 있음"
    }}
  ]
}}

JSON 형식으로만 응답해주세요.
"""
        return prompt

    def classify_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        기사 배치 분류

        Args:
            articles: 기사 리스트
                [{
                    'id': int,
                    'title': str,
                    'description': str (optional)
                }]

        Returns:
            분류 결과 리스트
                [{
                    'id': int,
                    'categories': List[str],
                    'tags': List[str],
                    'confidence': int,
                    'reasoning': str
                }]
        """
        if not articles:
            return []

        # Rate limiting 체크
        self._check_rate_limit()

        try:
            prompt = self._create_classification_prompt(articles)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 부동산 뉴스 분류 전문가입니다. JSON 형식으로만 응답하세요."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            classifications = result.get("classifications", [])

            # 검증: ID가 모두 있는지 확인
            article_ids = {art['id'] for art in articles}
            classified_ids = {cls.get('id') for cls in classifications}

            if not classified_ids.issubset(article_ids):
                print(f"Warning: Mismatched article IDs in classification result")

            return classifications

        except Exception as e:
            print(f"AI classification failed: {e}")
            # Fallback: 빈 분류 반환
            return [
                {
                    'id': art['id'],
                    'categories': [],
                    'tags': [],
                    'confidence': 0,
                    'reasoning': f'분류 실패: {str(e)}'
                }
                for art in articles
            ]

    def classify_batch(self, articles: List[Dict], batch_size: int = 10) -> Dict[int, Dict]:
        """
        대량 기사 배치 분류

        Args:
            articles: 기사 리스트
            batch_size: 배치 크기 (기본 10)

        Returns:
            {article_id: classification_result} 딕셔너리
        """
        results = {}
        total_batches = (len(articles) + batch_size - 1) // batch_size

        print(f"AI Classification: {len(articles)} articles in {total_batches} batches")

        for i in range(0, len(articles), batch_size):
            batch = articles[i:i+batch_size]
            batch_num = i // batch_size + 1

            print(f"  Batch {batch_num}/{total_batches}: {len(batch)} articles...")

            classifications = self.classify_articles(batch)

            # 결과 매핑
            for cls in classifications:
                article_id = cls.get('id')
                if article_id:
                    results[article_id] = cls

            # 배치 간 짧은 대기 (rate limiting 완화)
            if i + batch_size < len(articles):
                time.sleep(0.5)

        print(f"  Classified: {len(results)}/{len(articles)} articles")

        return results


def main():
    """테스트 코드"""
    print("=" * 80)
    print("AI Classifier Test (GPT-4o-mini)")
    print("=" * 80)

    # 테스트 데이터
    test_articles = [
        {
            'id': 1,
            'title': '정부, DSR 규제 강화 검토... 대출 한도 축소 전망',
            'description': '금융당국이 총부채원리금상환비율(DSR) 규제를 강화하는 방안을 검토 중이다.'
        },
        {
            'id': 2,
            'title': '서울 아파트 매매가 0.5% 상승... 강남 중심 상승세',
            'description': '이번 주 서울 아파트 매매가격이 전주 대비 0.5% 상승했다.'
        },
        {
            'id': 3,
            'title': '3기 신도시 예정지 토지 거래 급증... 투기 우려',
            'description': '3기 신도시 예정지의 토지 거래가 급증하며 투기 우려가 커지고 있다.'
        }
    ]

    # 분류기 생성
    classifier = AIClassifier()

    # 분류 실행
    results = classifier.classify_batch(test_articles, batch_size=10)

    # 결과 출력
    print("\n" + "=" * 80)
    print("Classification Results")
    print("=" * 80)

    for article_id, result in results.items():
        article = next((a for a in test_articles if a['id'] == article_id), None)
        if article:
            print(f"\nID {article_id}: {article['title']}")
            print(f"  Categories: {', '.join([CATEGORIES.get(c, c) for c in result.get('categories', [])])}")
            print(f"  Tags: {', '.join(result.get('tags', []))}")
            print(f"  Confidence: {result.get('confidence', 0)}%")
            print(f"  Reasoning: {result.get('reasoning', 'N/A')}")

    print("\n" + "=" * 80)
    print("[SUCCESS] Test completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
