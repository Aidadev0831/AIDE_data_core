"""AIDE Data Pipeline - Unified data collection and processing orchestrator

This package provides a centralized orchestrator for managing all data collection
and processing tasks in the AIDE Platform.

Features:
- Scheduled data collection from multiple sources
- Automated processing pipeline (embedding, deduplication, classification)
- Job execution tracking and error handling
- CLI interface for manual execution and monitoring

Usage:
    # Run all jobs
    python -m aide_pipeline run all

    # Run specific job
    python -m aide_pipeline run naver_news

    # Start scheduler
    python -m aide_pipeline schedule

    # Check job status
    python -m aide_pipeline status
"""

__version__ = "0.1.0"
__author__ = "AIDE Team"
