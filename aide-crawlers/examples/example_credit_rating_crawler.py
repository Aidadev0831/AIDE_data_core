"""
Example: Credit Rating Crawlers

This example demonstrates how to crawl credit rating research reports.
"""

from aide_crawlers.crawlers.credit_rating import KISRatingCrawler, KoreaRatingsCrawler
from aide_crawlers.sinks import LocalSink


def example_kisrating():
    """Example: Crawl KIS Rating research reports"""
    print("=" * 80)
    print("Example 1: KIS Rating Crawler")
    print("=" * 80)

    with LocalSink(output_dir="data/kisrating") as sink:
        with KISRatingCrawler(sink=sink, headless=True, max_pages=2) as crawler:
            result = crawler.run()

            print(f"\nResults:")
            print(f"  Created: {result['created']}")
            print(f"  Duplicates: {result['duplicates']}")
            print(f"  Failed: {result['failed']}")


def example_korearatings():
    """Example: Crawl Korea Ratings research reports"""
    print("\n" + "=" * 80)
    print("Example 2: Korea Ratings Crawler")
    print("=" * 80)

    with LocalSink(output_dir="data/korearatings") as sink:
        with KoreaRatingsCrawler(sink=sink, headless=True, max_pages=2) as crawler:
            result = crawler.run()

            print(f"\nResults:")
            print(f"  Created: {result['created']}")
            print(f"  Duplicates: {result['duplicates']}")
            print(f"  Failed: {result['failed']}")


def example_combined():
    """Example: Crawl both agencies and combine results"""
    print("\n" + "=" * 80)
    print("Example 3: Combined Crawling")
    print("=" * 80)

    all_results = {
        'created': 0,
        'duplicates': 0,
        'failed': 0
    }

    # Crawl KIS Rating
    with LocalSink(output_dir="data/credit_rating") as sink:
        print("\n1. Crawling KIS Rating...")
        with KISRatingCrawler(sink=sink, headless=True, max_pages=2) as crawler:
            result = crawler.run()
            all_results['created'] += result['created']
            all_results['duplicates'] += result['duplicates']
            all_results['failed'] += result['failed']

    # Crawl Korea Ratings
    with LocalSink(output_dir="data/credit_rating") as sink:
        print("\n2. Crawling Korea Ratings...")
        with KoreaRatingsCrawler(sink=sink, headless=True, max_pages=2) as crawler:
            result = crawler.run()
            all_results['created'] += result['created']
            all_results['duplicates'] += result['duplicates']
            all_results['failed'] += result['failed']

    print(f"\nCombined Results:")
    print(f"  Total Created: {all_results['created']}")
    print(f"  Total Duplicates: {all_results['duplicates']}")
    print(f"  Total Failed: {all_results['failed']}")


if __name__ == "__main__":
    # Run examples
    example_kisrating()
    example_korearatings()
    example_combined()

    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80)
