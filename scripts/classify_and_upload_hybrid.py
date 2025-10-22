#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
하이브리드 분류 (키워드 + AI) 후 Notion 업로드 (클러스터링 포함)

- 키워드 기반 분류 (빠름, 무료)
- AI 기반 분류 (정확함, 비용 발생)
- 두 결과를 병합하여 최적의 분류 수행
"""
import sys
import os
import json
import requests
from pathlib import Path
from datetime import datetime, date

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "aide-data-core"))
sys.path.insert(0, str(project_root / "scripts"))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aide_data_core.models import NaverNews

# 클러스터링 서비스 import
from clustering_service import apply_clustering_to_articles

# AI 분류 서비스 import
from ai_classifier import AIClassifier

# AI 분류 활성화 여부 (환경변수로 제어 가능)
USE_AI_CLASSIFICATION = os.getenv("USE_AI_CLASSIFICATION", "true").lower() == "true"
AI_CONFIDENCE_THRESHOLD = int(os.getenv("AI_CONFIDENCE_THRESHOLD", "70"))  # 70% 이상 신뢰도만 사용

# Notion 설정
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_API_VERSION = "2022-06-28"

# 카테고리 페이지 매핑 (insight_test에서)
CATEGORY_PAGES = {
    "policy_regulation": "28c18b63af4d80d9ba62c35619d4ad10",
    "market_transaction": "28c18b63af4d809e8021c3e407f622ee",
    "development_supply": "28c18b63af4d80f78093fe7512abae46",
    "finance_investment": "28c18b63af4d8013bbd0d6cd187f37a1",
    "construction_development": "28c18b63af4d80118c2ae66a33376c7b",
    "construction": "28c18b63af4d80749894d35875e59542",
    "commercial_realestate": "28c18b63af4d805ea7b1da7fa10a0e87",
    "auction_public_sale": "28c18b63af4d80baa436e66c7464845e",
}

CATEGORY_NAMES = {
    "policy_regulation": "정책·규제",
    "market_transaction": "시장동향",
    "development_supply": "분양·입주",
    "finance_investment": "금융·투자",
    "construction_development": "개발·사업",
    "construction": "건설·시공",
    "commercial_realestate": "상업용 부동산",
    "auction_public_sale": "경매·공매",
}

# 키워드 기반 카테고리 매핑 (확장판)
KEYWORD_CATEGORY_MAP = {
    # 정책·규제
    "정책": "policy_regulation",
    "규제": "policy_regulation",
    "정부": "policy_regulation",
    "법": "policy_regulation",
    "세금": "policy_regulation",
    "과세": "policy_regulation",
    "취득세": "policy_regulation",
    "양도세": "policy_regulation",
    "종부세": "policy_regulation",

    # 시장동향
    "시장": "market_transaction",
    "거래": "market_transaction",
    "가격": "market_transaction",
    "매매": "market_transaction",
    "부동산": "market_transaction",
    "아파트": "market_transaction",
    "주택": "market_transaction",
    "시세": "market_transaction",
    "하락": "market_transaction",
    "상승": "market_transaction",
    "임대": "market_transaction",
    "전세": "market_transaction",
    "월세": "market_transaction",
    "집값": "market_transaction",

    # 분양·입주
    "분양": "development_supply",
    "청약": "development_supply",
    "입주": "development_supply",
    "공급": "development_supply",
    "신축": "development_supply",
    "모델하우스": "development_supply",

    # 금융·투자
    "금리": "finance_investment",
    "대출": "finance_investment",
    "투자": "finance_investment",
    "은행": "finance_investment",
    "금융": "finance_investment",
    "담보": "finance_investment",
    "이자": "finance_investment",
    "주담대": "finance_investment",

    # 개발·사업
    "재개발": "construction_development",
    "재건축": "construction_development",
    "개발": "construction_development",
    "정비": "construction_development",
    "사업": "construction_development",
    "도시개발": "construction_development",

    # 건설·시공
    "건설": "construction",
    "시공": "construction",
    "시공사": "construction",
    "건설사": "construction",
    "착공": "construction",

    # 상업용 부동산
    "상가": "commercial_realestate",
    "오피스": "commercial_realestate",
    "빌딩": "commercial_realestate",
    "상업": "commercial_realestate",
    "사무실": "commercial_realestate",
    "점포": "commercial_realestate",

    # 경매·공매
    "경매": "auction_public_sale",
    "공매": "auction_public_sale",
    "유찰": "auction_public_sale",
}


def classify_article_keyword(title: str, description: str = "") -> list:
    """키워드 기반 간단 분류"""
    text = f"{title} {description}".lower()
    categories = []

    for keyword, category in KEYWORD_CATEGORY_MAP.items():
        if keyword in text:
            if category not in categories:
                categories.append(category)

    # 기본 카테고리 (분류 안되면)
    if not categories:
        categories = ["market_transaction"]

    return categories


def merge_classifications(keyword_categories: list, ai_result: dict) -> dict:
    """
    키워드 분류와 AI 분류 병합

    Args:
        keyword_categories: 키워드 기반 카테고리 리스트
        ai_result: AI 분류 결과 dict
            {
                'categories': list,
                'tags': list,
                'confidence': int,
                'reasoning': str
            }

    Returns:
        {
            'categories': list,  # 최종 카테고리
            'tags': list,        # AI 태그
            'confidence': int,   # AI 신뢰도
            'reasoning': str,    # AI 판단 근거
            'method': str        # 분류 방법 (keyword, ai, hybrid)
        }
    """
    # AI 신뢰도가 임계값 이상이면 AI 우선
    if ai_result.get('confidence', 0) >= AI_CONFIDENCE_THRESHOLD:
        return {
            'categories': ai_result.get('categories', keyword_categories),
            'tags': ai_result.get('tags', []),
            'confidence': ai_result.get('confidence', 0),
            'reasoning': ai_result.get('reasoning', ''),
            'method': 'ai'
        }

    # AI 신뢰도가 낮으면 하이브리드 (키워드 + AI 카테고리 합침)
    else:
        merged_categories = list(set(keyword_categories + ai_result.get('categories', [])))
        return {
            'categories': merged_categories if merged_categories else keyword_categories,
            'tags': ai_result.get('tags', []),
            'confidence': ai_result.get('confidence', 0),
            'reasoning': ai_result.get('reasoning', 'Hybrid: 키워드 + AI 병합'),
            'method': 'hybrid'
        }


def get_notion_headers():
    """Notion API 헤더"""
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION
    }


def delete_blocks_from_page(page_id: str, start_index: int = 2):
    """페이지의 특정 인덱스부터 블록 삭제"""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    response = requests.get(url, headers=get_notion_headers(), timeout=30)

    if response.status_code != 200:
        return False

    blocks = response.json().get("results", [])
    blocks_to_delete = blocks[start_index:]

    for block in blocks_to_delete:
        delete_url = f"https://api.notion.com/v1/blocks/{block['id']}"
        requests.delete(delete_url, headers=get_notion_headers(), timeout=30)

    return True


def append_blocks_to_page(page_id: str, blocks: list):
    """페이지에 블록 추가"""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    response = requests.patch(
        url,
        headers=get_notion_headers(),
        json={"children": blocks},
        timeout=30
    )
    return response.status_code == 200


def create_empty_block():
    """빈 블록 생성"""
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": ""}}]}
    }


def create_footer_blocks(logo_url: str = None):
    """푸터 블록 생성"""
    blocks = []

    # 3개의 빈 줄
    for _ in range(3):
        blocks.append(create_empty_block())

    # 로고 이미지 (있으면)
    if logo_url:
        blocks.append({
            "object": "block",
            "type": "image",
            "image": {
                "type": "external",
                "external": {"url": logo_url}
            }
        })

    # 회사 브랜드
    blocks.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "부동산 비즈니스 전문가를 위한\n🟦 AIDE INSIGHT | 에이드 인사이트"},
                "annotations": {"bold": True}
            }]
        }
    })

    # 회사 정보
    blocks.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "(주)에이드파트너스 | 대표이사: 송인근 | 사업자등록번호: 345-81-02007\n서울특별시 서초구 강남대로97길 26, 4층\n© 2025 AIDE Partners Co., Ltd. All rights reserved"}
            }]
        }
    })

    return blocks


def create_article_blocks(date_str: str, category_name: str, articles: list):
    """기사 블록 생성"""
    blocks = []

    # 헤더
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    heading = f"{dt.year}년 {dt.month}월 {dt.day}일, {category_name} 소식입니다"

    blocks.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "type": "text",
                "text": {"content": heading},
                "annotations": {"bold": True}
            }]
        }
    })

    # 구분선
    blocks.append({
        "object": "block",
        "type": "divider",
        "divider": {}
    })

    # 기사 목록
    for article in articles:
        # 기사제목[1건] 🔗 형식
        rich_text = [
            {"type": "text", "text": {"content": f"{article['title']}[{article.get('cluster_size', 1)}건] "}},
            {"type": "text", "text": {"content": "🔗", "link": {"url": article['url']}}}
        ]

        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": rich_text}
        })

    # 푸터 추가
    footer_blocks = create_footer_blocks(logo_url="https://www.aidepartners.com/images/logo.png")
    blocks.extend(footer_blocks)

    return blocks


def main():
    """메인 프로세스"""
    print("=" * 80)
    print("Hybrid Classify (Keyword + AI) & Upload to Notion")
    print("=" * 80)
    print(f"Date: {date.today().isoformat()}")
    print(f"AI Classification: {'ENABLED' if USE_AI_CLASSIFICATION else 'DISABLED'}")
    print(f"AI Confidence Threshold: {AI_CONFIDENCE_THRESHOLD}%\n")

    # DB 연결
    db_url = "sqlite:///" + str(project_root / "aide-data-core" / "aide_dev.db")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    # AI 분류기 초기화
    ai_classifier = None
    if USE_AI_CLASSIFICATION:
        try:
            ai_classifier = AIClassifier()
            print("AI Classifier initialized (GPT-4o-mini)\n")
        except Exception as e:
            print(f"AI Classifier initialization failed: {e}")
            print("Falling back to keyword-only classification\n")

    try:
        # 1. 모든 raw 기사 조회
        articles = db.query(NaverNews).filter(
            NaverNews.status == 'raw'
        ).order_by(NaverNews.date.desc()).all()

        print(f"Found: {len(articles)} articles to process\n")

        if len(articles) == 0:
            print("No raw articles to process. All done!")
            db.close()
            return 0

        # 2. 키워드 분류
        print("Step 1: Keyword-based classification...")
        keyword_classifications = {}
        for article in articles:
            keyword_classifications[article.id] = classify_article_keyword(
                article.title,
                article.description or ""
            )
        print(f"  Classified {len(keyword_classifications)} articles by keywords\n")

        # 3. AI 분류 (활성화된 경우)
        ai_classifications = {}
        if ai_classifier:
            print("Step 2: AI-based classification (GPT-4o-mini)...")

            # 기사 데이터 준비
            articles_for_ai = [
                {
                    'id': article.id,
                    'title': article.title,
                    'description': article.description or ''
                }
                for article in articles
            ]

            # 배치 AI 분류
            ai_classifications = ai_classifier.classify_batch(articles_for_ai, batch_size=10)
            print(f"  AI classified {len(ai_classifications)} articles\n")
        else:
            print("Step 2: AI classification SKIPPED (disabled or failed)\n")

        # 4. 키워드 + AI 병합
        print("Step 3: Merging keyword and AI classifications...")
        articles_by_category = {cat: [] for cat in CATEGORY_PAGES.keys()}
        classification_stats = {'keyword': 0, 'ai': 0, 'hybrid': 0}

        for article in articles:
            keyword_cats = keyword_classifications.get(article.id, ["market_transaction"])
            ai_result = ai_classifications.get(article.id, {})

            # 병합
            merged = merge_classifications(keyword_cats, ai_result)
            final_categories = merged['categories']

            # 통계
            classification_stats[merged['method']] += 1

            # 카테고리에 기사 추가
            for cat_code in final_categories:
                if cat_code in articles_by_category:
                    articles_by_category[cat_code].append({
                        'title': article.title,
                        'url': article.url,
                        'id': article.id,
                        'description': article.description or '',
                        'source': article.source or '기타'
                    })

            # DB 업데이트
            article.classified_categories = json.dumps(
                [CATEGORY_NAMES.get(c, c) for c in final_categories],
                ensure_ascii=False
            )
            article.status = 'processed'
            article.cluster_representative = True

            # AI 결과 저장 (있으면)
            if merged.get('tags'):
                # 태그는 description에 임시 저장 (추후 별도 필드로 분리 가능)
                article.description = f"{article.description or ''}\n[AI Tags: {', '.join(merged['tags'])}]"

        db.commit()

        print(f"  Classification methods used:")
        print(f"    - Keyword only: {classification_stats['keyword']}")
        print(f"    - AI only: {classification_stats['ai']}")
        print(f"    - Hybrid: {classification_stats['hybrid']}")
        print()

        # 5. Notion 업로드
        print("Step 4: Uploading to Notion...\n")
        today_str = date.today().isoformat()

        for cat_code, cat_articles in articles_by_category.items():
            if not cat_articles:
                continue

            cat_name = CATEGORY_NAMES[cat_code]
            page_id = CATEGORY_PAGES[cat_code]

            # 클러스터링 적용 (유사 기사 그룹화)
            if len(cat_articles) > 1:
                print(f"[{cat_name}] {len(cat_articles)} articles -> clustering...")
                try:
                    representatives, _ = apply_clustering_to_articles(
                        cat_articles,
                        similarity_threshold=0.6
                    )
                    print(f"  Clustered: {len(representatives)} representatives")
                except Exception as e:
                    print(f"  Clustering failed: {e}, using all articles")
                    representatives = cat_articles
                    for art in representatives:
                        art['cluster_size'] = 1
            else:
                print(f"[{cat_name}] {len(cat_articles)} articles (no clustering needed)")
                representatives = cat_articles
                for art in representatives:
                    art['cluster_size'] = 1

            # 기존 블록 삭제 (3번째부터)
            delete_blocks_from_page(page_id, start_index=2)

            # 새 블록 추가 (상위 20개 대표 기사)
            blocks = create_article_blocks(today_str, cat_name, representatives[:20])
            append_blocks_to_page(page_id, blocks)

        print("\n" + "=" * 80)
        print("[SUCCESS] Hybrid classification and upload completed!")
        print("=" * 80)

        db.close()
        return 0

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        db.close()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
