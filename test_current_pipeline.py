
import logging
from discovery.edu_search_pipeline import EduSearchPipeline, setup_logger

# Setup logging
setup_logger(level=logging.INFO)

pipeline = EduSearchPipeline()

print("\n--- Testing Current Pipeline Logic ---")
try:
    # Test a query that might be failing
    results = pipeline.search(
        grade=4,
        subject="Chemistry",
        topic="atoms",
        content_types=["concept_explainer"],
        max_results=5,
        strict_domain_filter=True # Trying strict first as per current logic usually prefers
    )
    print(f"Found {len(results)} results.")
    for r in results:
        print(f"- {r.title} ({r.url})")
except Exception as e:
    print(f"Error: {e}")

print("\n--- End Test ---")
