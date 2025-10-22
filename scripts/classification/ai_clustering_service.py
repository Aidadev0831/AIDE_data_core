#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 기반 유사도 클러스터링 서비스 (OpenAI Embeddings)

TF-IDF 대신 OpenAI Embeddings를 사용하여 의미론적 유사도 계산
"""
import os
import numpy as np
from typing import List, Dict, Tuple
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()


class AIClusteringService:
    """AI 기반 유사 기사 클러스터링 (OpenAI Embeddings)"""

    def __init__(self, similarity_threshold: float = 0.7):
        """
        Args:
            similarity_threshold: 유사도 임계값 (0.7 = 70% 이상 유사하면 같은 클러스터)
        """
        self.similarity_threshold = similarity_threshold
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "text-embedding-3-small"  # 1536 차원, 저렴함

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        텍스트들을 임베딩 벡터로 변환

        Args:
            texts: 텍스트 리스트

        Returns:
            embeddings: (n, 1536) 형태의 numpy array
        """
        # OpenAI API는 한 번에 최대 2048개 텍스트 처리 가능
        # 긴 텍스트는 자동으로 8191 토큰으로 잘림

        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )

        # 임베딩 추출
        embeddings = [item.embedding for item in response.data]
        return np.array(embeddings)

    def cluster_articles(self, articles: List[Dict]) -> Dict[int, List[Dict]]:
        """
        기사들을 AI 기반 유사도로 클러스터링

        Args:
            articles: [{'id': 1, 'title': '...', 'description': '...', ...}, ...]

        Returns:
            {cluster_id: [article1, article2, ...], ...}
        """
        if not articles:
            return {}

        # 텍스트 준비 (제목 + 설명)
        texts = []
        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}"
            texts.append(text)

        # AI 임베딩 생성
        print(f"  AI Embeddings: {len(texts)} articles...")
        embeddings = self.get_embeddings(texts)

        # 코사인 유사도 계산
        similarity_matrix = cosine_similarity(embeddings)

        # 클러스터링 (유사도 기반 그룹화)
        clusters = self._group_by_similarity(similarity_matrix, articles)

        return clusters

    def _group_by_similarity(
        self,
        similarity_matrix: np.ndarray,
        articles: List[Dict]
    ) -> Dict[int, List[Dict]]:
        """유사도 매트릭스를 기반으로 그룹화"""
        n = len(articles)
        visited = set()
        clusters = {}
        cluster_id = 0

        for i in range(n):
            if i in visited:
                continue

            # 새 클러스터 시작
            cluster = [articles[i]]
            visited.add(i)

            # 유사한 기사 찾기
            for j in range(i + 1, n):
                if j in visited:
                    continue

                if similarity_matrix[i, j] >= self.similarity_threshold:
                    cluster.append(articles[j])
                    visited.add(j)

            # 클러스터가 2개 이상 기사를 가지면 저장
            if len(cluster) >= 2:
                clusters[cluster_id] = cluster
                cluster_id += 1

        return clusters

    def select_representative(self, cluster: List[Dict]) -> Dict:
        """
        클러스터에서 대표 기사 선정

        기준:
        1. 신뢰할 수 있는 언론사 우선
        2. 제목 + 설명 길이가 긴 기사 우선

        Args:
            cluster: 같은 클러스터의 기사 리스트

        Returns:
            대표 기사
        """
        if len(cluster) == 1:
            return cluster[0]

        # 신뢰 언론사 목록
        trusted_sources = {
            "조선일보", "중앙일보", "동아일보",
            "한국경제", "매일경제", "서울경제",
            "한겨레", "경향신문"
        }

        # 점수 계산
        scored = []
        for article in cluster:
            source = article.get('source', '')
            title = article.get('title', '')
            description = article.get('description', '')

            # 신뢰도 점수
            reliability_score = 1.0 if source in trusted_sources else 0.3

            # 정보량 점수 (길이 기반)
            info_score = min((len(title) + len(description)) / 500.0, 1.0)

            # 종합 점수 (50% + 50%)
            total_score = 0.5 * reliability_score + 0.5 * info_score

            scored.append((total_score, article))

        # 점수 높은 순으로 정렬
        scored.sort(key=lambda x: x[0], reverse=True)

        return scored[0][1]

    def get_cluster_stats(self, clusters: Dict[int, List[Dict]]) -> Dict:
        """클러스터링 통계"""
        total_articles = sum(len(cluster) for cluster in clusters.values())
        cluster_sizes = [len(cluster) for cluster in clusters.values()]

        return {
            'num_clusters': len(clusters),
            'total_articles_in_clusters': total_articles,
            'avg_cluster_size': np.mean(cluster_sizes) if cluster_sizes else 0,
            'max_cluster_size': max(cluster_sizes) if cluster_sizes else 0,
            'min_cluster_size': min(cluster_sizes) if cluster_sizes else 0
        }


def apply_ai_clustering_to_articles(
    articles: List[Dict],
    similarity_threshold: float = 0.7
) -> Tuple[List[Dict], Dict[int, int]]:
    """
    기사들에 AI 클러스터링 적용하고 대표 기사 선정

    Args:
        articles: 기사 리스트
        similarity_threshold: 유사도 임계값

    Returns:
        (representatives, article_to_cluster)
        - representatives: 대표 기사 리스트 (클러스터 크기 포함)
        - article_to_cluster: {article_id: cluster_id} 매핑
    """
    service = AIClusteringService(similarity_threshold=similarity_threshold)

    # 클러스터링
    clusters = service.cluster_articles(articles)

    # 통계
    stats = service.get_cluster_stats(clusters)
    print(f"  AI 클러스터링 통계: {stats}")

    # 대표 기사 선정
    representatives = []
    article_to_cluster = {}

    # 클러스터에 속한 기사들
    for cluster_id, cluster_articles in clusters.items():
        # 대표 기사 선정
        rep = service.select_representative(cluster_articles)
        rep['cluster_size'] = len(cluster_articles)  # 클러스터 크기 추가
        rep['cluster_id'] = cluster_id
        representatives.append(rep)

        # article_id -> cluster_id 매핑
        for article in cluster_articles:
            article_to_cluster[article['id']] = cluster_id

    # 클러스터에 속하지 않은 기사들 (단독 기사)
    clustered_ids = set(article_to_cluster.keys())
    for article in articles:
        if article['id'] not in clustered_ids:
            article['cluster_size'] = 1  # 단독 기사
            article['cluster_id'] = -1  # 클러스터 없음
            representatives.append(article)

    return representatives, article_to_cluster


if __name__ == "__main__":
    # 테스트
    print("=" * 80)
    print("AI Clustering Test (OpenAI Embeddings)")
    print("=" * 80)

    test_articles = [
        {
            'id': 1,
            'title': '서울 아파트 가격 상승세 지속',
            'description': '서울 지역 아파트 가격이 계속해서 오르고 있습니다.',
            'source': '조선일보'
        },
        {
            'id': 2,
            'title': '서울 아파트값 계속 올라',  # 의미상 기사1과 유사
            'description': '서울 아파트 가격 상승이 이어지고 있다.',
            'source': '기타'
        },
        {
            'id': 3,
            'title': '서울 주택 시세 증가',  # "주택" = "아파트" (AI가 인식 가능)
            'description': '서울 주택 가격이 올랐습니다.',
            'source': '중앙일보'
        },
        {
            'id': 4,
            'title': '금리 인상 단행',  # 완전히 다른 주제
            'description': '한국은행이 기준금리를 인상했습니다.',
            'source': '한국경제'
        },
    ]

    representatives, mapping = apply_ai_clustering_to_articles(
        test_articles,
        similarity_threshold=0.75  # AI는 더 정확하므로 임계값 높게 설정
    )

    print("\n대표 기사:")
    for rep in representatives:
        print(f"  ID {rep['id']}: {rep['title']} [{rep['cluster_size']}건]")

    print(f"\n클러스터 매핑: {mapping}")
    print("\n" + "=" * 80)
