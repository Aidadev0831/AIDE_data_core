"""
Example: KDI Policy Crawler

This example demonstrates how to crawl KDI policy documents.
"""

from aide_crawlers.crawlers.research import KDIPolicyCrawler
from aide_crawlers.sinks import LocalSink, DBSink
from aide_data_core.models import NaverNews  # TODO: Use KDIPolicy model


def example_local_sink():
    """Example: Save KDI documents to local JSON files"""
    print("=" * 80)
    print("Example 1: KDI Crawler → Local JSON")
    print("=" * 80)

    # Create local sink
    sink = LocalSink(output_dir="data/kdi", format="json")

    # Create crawler
    crawler = KDIPolicyCrawler(
        sink=sink,
        headless=True,
        max_pages=2,
        days_back=30
    )

    # Run crawler
    result = crawler.run()

    print(f"\nResults:")
    print(f"  Created: {result['created']}")
    print(f"  Duplicates: {result['duplicates']}")
    print(f"  Failed: {result['failed']}")

    # Cleanup
    crawler.close()


def example_db_sink():
    """Example: Save KDI documents to database"""
    print("\n" + "=" * 80)
    print("Example 2: KDI Crawler → Database")
    print("=" * 80)

    # Create DB sink
    # TODO: Change to KDIPolicy model when created
    sink = DBSink(
        database_url="sqlite:///./aide_dev.db",
        target_table="domain",
        model_class=NaverNews  # Temporary: use NaverNews as placeholder
    )

    # Create crawler with job logging
    crawler = KDIPolicyCrawler(
        sink=sink,
        headless=True,
        max_pages=2,
        days_back=30,
        database_url="sqlite:///./aide_dev.db"
    )

    # Run crawler
    result = crawler.run()

    print(f"\nResults:")
    print(f"  Created: {result['created']}")
    print(f"  Duplicates: {result['duplicates']}")
    print(f"  Failed: {result['failed']}")

    # Cleanup
    crawler.close()


def example_context_manager():
    """Example: Using context manager"""
    print("\n" + "=" * 80)
    print("Example 3: Using Context Manager")
    print("=" * 80)

    with LocalSink(output_dir="data/kdi") as sink:
        with KDIPolicyCrawler(sink=sink, headless=True, max_pages=1) as crawler:
            result = crawler.run()
            print(f"\nCreated {result['created']} documents")


if __name__ == "__main__":
    # Run examples
    example_local_sink()
    example_db_sink()
    example_context_manager()

    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80)
