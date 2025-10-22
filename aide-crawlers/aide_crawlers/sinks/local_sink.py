"""
Local Sink - File Storage

Stores crawled data to local files (JSON or CSV).
Useful for backups, debugging, and offline processing.
"""

from typing import List
from pydantic import BaseModel
from pathlib import Path
import json
import csv
from datetime import datetime

from ..utils.logger import setup_logger
from .abstract import AbstractSink, SinkResult

logger = setup_logger("local_sink", format_type="text")


class LocalSink(AbstractSink):
    """로컬 파일 저장 Sink

    JSON 또는 CSV 형식으로 로컬 파일 시스템에 저장합니다.

    Example:
        >>> from aide_crawlers.sinks import LocalSink
        >>> from aide_data_core.schemas import NaverNewsCreate
        >>>
        >>> # JSON format
        >>> sink = LocalSink(output_dir="data", format="json")
        >>> result = sink.write([NaverNewsCreate(...)])
        >>> sink.close()
        >>>
        >>> # CSV format
        >>> sink = LocalSink(output_dir="data", format="csv")
        >>> result = sink.write([NaverNewsCreate(...)])
        >>> sink.close()
    """

    def __init__(
        self,
        output_dir: str = "data",
        format: str = "json"
    ):
        """Initialize LocalSink

        Args:
            output_dir: Output directory path
            format: File format ("json" or "csv")
        """
        self.output_dir = Path(output_dir)
        self.format = format.lower()

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"LocalSink initialized: dir={output_dir}, format={format}")

    def write(self, items: List[BaseModel]) -> SinkResult:
        """Write items to local file

        Creates a timestamped file for each batch.

        Args:
            items: List of Pydantic schema instances

        Returns:
            SinkResult with counts
        """
        logger.info(f"LocalSink.write() called with {len(items)} items")

        result: SinkResult = {
            "created": 0,
            "updated": 0,
            "duplicates": 0,
            "failed": 0
        }

        if not items:
            return result

        try:
            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            source = getattr(items[0], 'source', 'unknown')
            filename = f"{source}_{timestamp}.{self.format}"
            filepath = self.output_dir / filename

            # Write to file
            if self.format == "json":
                self._write_json(filepath, items)
            elif self.format == "csv":
                self._write_csv(filepath, items)
            else:
                raise ValueError(f"Unsupported format: {self.format}")

            result['created'] = len(items)
            logger.info(f"Saved {len(items)} items to {filepath}")

        except Exception as e:
            logger.error(f"Failed to write to local file: {str(e)}")
            result['failed'] = len(items)

        return result

    def _write_json(self, filepath: Path, items: List[BaseModel]):
        """Write items to JSON file"""
        data = [item.model_dump(mode='json') for item in items]

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _write_csv(self, filepath: Path, items: List[BaseModel]):
        """Write items to CSV file"""
        if not items:
            return

        # Get field names from first item
        fieldnames = items[0].model_dump().keys()

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for item in items:
                # Convert complex fields to JSON strings
                row = {}
                for key, value in item.model_dump().items():
                    if isinstance(value, (dict, list)):
                        row[key] = json.dumps(value, ensure_ascii=False)
                    elif isinstance(value, datetime):
                        row[key] = value.isoformat()
                    else:
                        row[key] = value

                writer.writerow(row)

    def close(self):
        """No resources to close for file-based sink"""
        logger.info("LocalSink closed")
