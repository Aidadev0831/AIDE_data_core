"""
Sinks 추상화

Sink는 크롤링된 데이터를 저장하는 추상 인터페이스입니다.
- DBSink: 데이터베이스 직접 저장
- LocalSink: 로컬 파일 저장 (JSON/CSV)
- APISink: REST API 전송 (Project 4 완성 후)
"""

from abc import ABC, abstractmethod
from typing import List, TypedDict
from pydantic import BaseModel


class SinkResult(TypedDict):
    """Sink 실행 결과

    Attributes:
        created: 새로 생성된 아이템 수
        updated: 업데이트된 아이템 수
        duplicates: 중복으로 건너뛴 아이템 수
        failed: 실패한 아이템 수
    """
    created: int
    updated: int
    duplicates: int
    failed: int


class AbstractSink(ABC):
    """추상 Sink 클래스

    모든 Sink는 이 클래스를 상속받아 write()와 close()를 구현해야 합니다.

    Example:
        >>> from aide_data_core.schemas import NaverNewsCreate
        >>> from aide_crawlers.sinks import DBSink
        >>>
        >>> sink = DBSink(target_table="domain")
        >>> items = [NaverNewsCreate(...), NaverNewsCreate(...)]
        >>> result = sink.write(items)
        >>> print(result)  # {"created": 2, "updated": 0, "duplicates": 0, "failed": 0}
        >>> sink.close()
    """

    @abstractmethod
    def write(self, items: List[BaseModel]) -> SinkResult:
        """아이템을 Sink에 기록

        Args:
            items: AIDE Data Core Pydantic 스키마 인스턴스 리스트
                   (예: NaverNewsCreate, KDIPolicyCreate 등)

        Returns:
            SinkResult: 처리 결과 통계

        Raises:
            NotImplementedError: 서브클래스에서 구현 필요
        """
        pass

    @abstractmethod
    def close(self):
        """리소스 정리

        데이터베이스 세션, HTTP 클라이언트, 파일 핸들 등을 정리합니다.
        """
        pass

    def __enter__(self):
        """Context manager 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.close()
        return False
