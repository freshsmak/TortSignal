"""
UniCourt Product Liability Discovery - Proper Implementation

Based on real-world field guidance, this implements the 3-query strategy:
- Query A: New potential product liability (high recall)
- Query B: New tort-language cases (high precision)
- Query C: Recent updates to existing cases

Key insight: DON'T search for product names. Search by STRUCTURE,
then extract products from results.
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Check if UniCourt SDK is available
try:
    import unicourt
    from unicourt import Authentication, CaseSearch
    UNICOURT_AVAILABLE = True
except ImportError:
    UNICOURT_AVAILABLE = False
    print("⚠️  UniCourt SDK not available. Install with: pip install unicourt")
    exit(1)

# Configure credentials
unicourt.CLIENT_ID = os.getenv("UNICOURT_CLIENT_ID")
unicourt.CLIENT_SECRET = os.getenv("UNICOURT_CLIENT_SECRET")

def authenticate():
    """Authenticate with UniCourt API."""
    print("Authenticating with UniCourt...")
    try:
        auth_obj, status_code = Authentication.generate_new_token()
        if status_code == 200:
            print("✓ Authentication successful\n")
            return True
        else:
            print(f"✗ Authentication failed: {status_code}")
            return False
    except Exception as e:
        print(f"✗ Authentication error: {e}")
        return False

def query_a_new_product_liability(days_back=2):
    """
    Query A: High recall - new defendants in recent cases.

    Strategy: Pull all cases with defendants filed recently.
    Let clustering identify which are product liability.

    Operator count: 2 (filedDate + Party constraint)
    """
    print("="*70)
    print("QUERY A: New Potential Product Liability Cases")
    print("="*70)

    since_date = datetime.now() - timedelta(days=days_back)
    date_str = since_date.strftime("%Y-%m-%d")

    # High recall query
    query = f'filedDate:[{date_str} TO *] AND (Party:((PartyRole:(name:defendant))))'

    print(f"\nQuery: {query}")
    print(f"Operator count: 2")
    print(f"Strategy: High recall - capture all defendant cases, filter later")
    print("\nSearching...\n")

    try:
        response, status = CaseSearch.search_cases(
            q=query,
            order='desc',
            sort='filedDate',
            page_number=1,
            page_size=100
        )

        if status == 200:
            cases = response.case_search_result_array or []
            print(f"✓ Found {len(cases)} cases with defendants")

            if hasattr(response, 'total_count'):
                print(f"  Total matching: {response.total_count}")

            # Sample first few
            if len(cases) > 0:
                print(f"\n{'#':<3} {'Filed':<12} {'Case Title':<50}")
                print("-"*70)

                for i, case in enumerate(cases[:10], 1):
                    filed = getattr(case, 'filed_date', 'Unknown')
                    title = getattr(case, 'title', getattr(case, 'case_name', 'No title'))
                    title_str = str(title)[:49]
                    print(f"{i:<3} {str(filed):<12} {title_str}")

                print(f"\n(Showing 10 of {len(cases)})")

            return cases

        else:
            print(f"✗ Search failed: {status}")
            return []

    except Exception as e:
        print(f"✗ Error: {e}")
        return []

def query_b_tort_language(days_back=2):
    """
    Query B: High precision - explicit tort language.

    Strategy: Catch cases where caption/docket mentions tort language,
    even if product isn't in title.

    Operator count: 5 (filedDate + 4 OR terms)
    """
    print("\n" + "="*70)
    print("QUERY B: Tort Language Detection")
    print("="*70)

    since_date = datetime.now() - timedelta(days=days_back)
    date_str = since_date.strftime("%Y-%m-%d")

    # High precision query with tort language
    query = f'filedDate:[{date_str} TO *] AND ("product liability" OR "design defect" OR "failure to warn" OR "strict liability")'

    print(f"\nQuery: {query}")
    print(f"Operator count: 5")
    print(f"Strategy: High precision - explicit tort language in docket/caption")
    print("\nSearching...\n")

    try:
        response, status = CaseSearch.search_cases(
            q=query,
            order='desc',
            sort='filedDate',
            page_number=1,
            page_size=100
        )

        if status == 200:
            cases = response.case_search_result_array or []
            print(f"✓ Found {len(cases)} cases with tort language")

            if hasattr(response, 'total_count'):
                print(f"  Total matching: {response.total_count}")

            # Sample first few
            if len(cases) > 0:
                print(f"\n{'#':<3} {'Filed':<12} {'Case Title':<50}")
                print("-"*70)

                for i, case in enumerate(cases[:10], 1):
                    filed = getattr(case, 'filed_date', 'Unknown')
                    title = getattr(case, 'title', getattr(case, 'case_name', 'No title'))
                    title_str = str(title)[:49]

                    # Highlight which keyword matched (if visible in title)
                    keywords = ['product liability', 'design defect', 'failure to warn', 'strict liability']
                    matched = [k for k in keywords if k.lower() in title_str.lower()]
                    marker = f" 🎯 [{matched[0]}]" if matched else ""

                    print(f"{i:<3} {str(filed):<12} {title_str}{marker}")

                print(f"\n(Showing 10 of {len(cases)})")

            return cases

        else:
            print(f"✗ Search failed: {status}")
            return []

    except Exception as e:
        print(f"✗ Error: {e}")
        return []

def query_c_recent_updates(days_back=2):
    """
    Query C: Monitoring stream - what changed recently.

    Strategy: Catch existing cases with new docket entries, parties, etc.
    Useful for tracking acceleration of known clusters.

    Operator count: 2 (lastFetchDateWithUpdates + Party constraint)
    """
    print("\n" + "="*70)
    print("QUERY C: Recent Case Updates")
    print("="*70)

    since_date = datetime.now() - timedelta(days=days_back)
    date_str = since_date.strftime("%Y-%m-%d")

    # Monitoring query
    query = f'(lastFetchDateWithUpdates:[{date_str} TO *]) AND (Party:((PartyRole:(name:defendant))))'

    print(f"\nQuery: {query}")
    print(f"Operator count: 2")
    print(f"Strategy: Monitoring - track changes to existing cases")
    print("\nSearching...\n")

    try:
        response, status = CaseSearch.search_cases(
            q=query,
            order='desc',
            sort='lastFetchDateWithUpdates',
            page_number=1,
            page_size=100
        )

        if status == 200:
            cases = response.case_search_result_array or []
            print(f"✓ Found {len(cases)} recently updated cases")

            if hasattr(response, 'total_count'):
                print(f"  Total matching: {response.total_count}")

            # Sample first few
            if len(cases) > 0:
                print(f"\n{'#':<3} {'Updated':<12} {'Case Title':<50}")
                print("-"*70)

                for i, case in enumerate(cases[:10], 1):
                    updated = getattr(case, 'last_fetch_date_with_updates', 'Unknown')
                    title = getattr(case, 'title', getattr(case, 'case_name', 'No title'))
                    title_str = str(title)[:49]
                    print(f"{i:<3} {str(updated):<12} {title_str}")

                print(f"\n(Showing 10 of {len(cases)})")

            return cases

        else:
            print(f"✗ Search failed: {status}")
            return []

    except Exception as e:
        print(f"✗ Error: {e}")
        return []

def discover_case_types():
    """
    Discovery step: Find what CaseType values correspond to product liability.

    This is the "one thing we still need" - mapping CaseType/AreaOfLaw to
    product liability categories.
    """
    print("\n" + "="*70)
    print("DISCOVERY: Identifying Product Liability Case Types")
    print("="*70)

    print("""
This is a one-time discovery step to identify which CaseType, AreaOfLaw,
and CauseOfAction values in UniCourt correspond to:
- Personal injury
- Product liability
- Toxic tort
- Consumer product harm
- Medical device / pharma injury

Strategy: Search for known product liability terms, then examine the
CaseType objects returned to identify the canonical values.
""")

    # Search for obvious product liability cases
    query = '("product liability" OR "defective product" OR "failure to warn")'

    print(f"\nQuery: {query}")
    print("Searching for sample cases to extract CaseType patterns...\n")

    try:
        response, status = CaseSearch.search_cases(
            q=query,
            order='desc',
            sort='filedDate',
            page_number=1,
            page_size=20
        )

        if status == 200:
            cases = response.case_search_result_array or []
            print(f"✓ Found {len(cases)} sample cases")

            # Extract unique case types
            case_types = set()
            areas_of_law = set()

            for case in cases:
                # Try to get case type
                if hasattr(case, 'case_type'):
                    ct = getattr(case, 'case_type', None)
                    if ct:
                        case_types.add(str(ct))

                # Try to get area of law
                if hasattr(case, 'area_of_law'):
                    aol = getattr(case, 'area_of_law', None)
                    if aol:
                        areas_of_law.add(str(aol))

            if case_types:
                print(f"\nUnique CaseType values found:")
                for ct in sorted(case_types):
                    print(f"  • {ct}")

            if areas_of_law:
                print(f"\nUnique AreaOfLaw values found:")
                for aol in sorted(areas_of_law):
                    print(f"  • {aol}")

            if not case_types and not areas_of_law:
                print("\n⚠️  Could not extract CaseType/AreaOfLaw from response objects")
                print("    Need to examine actual API response structure")

            return cases

        else:
            print(f"✗ Search failed: {status}")
            return []

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """Run all three discovery queries + case type discovery."""
    print("="*70)
    print("UNICOURT PRODUCT LIABILITY DISCOVERY")
    print("="*70)
    print()
    print("Strategy: 3-query approach under 15-operator limit")
    print("  Query A: High recall (all defendant cases)")
    print("  Query B: High precision (tort language)")
    print("  Query C: Monitoring (recent updates)")
    print()

    if not authenticate():
        return

    # Run all three queries
    days_back = 7  # Look back 1 week for demo

    query_a_results = query_a_new_product_liability(days_back=days_back)
    query_b_results = query_b_tort_language(days_back=days_back)
    query_c_results = query_c_recent_updates(days_back=days_back)

    # Case type discovery
    discover_case_types()

    # Summary
    print("\n" + "="*70)
    print("DISCOVERY SUMMARY")
    print("="*70)

    print(f"""
Results:
  Query A (High Recall):    {len(query_a_results)} cases
  Query B (High Precision): {len(query_b_results)} cases
  Query C (Monitoring):     {len(query_c_results)} cases

Next Steps:
1. Enrich each caseId with /case/{{id}}/parties + /attorneys
2. Extract: defendant names, products (from title/docket)
3. Create candidate rows in database
4. Run clustering on (defendant, product) pairs
5. Calculate velocity, breadth, score

Architecture Notes:
- These 3 queries stay under 15-operator limit
- Pull structure (defendant + date), not products
- Let clustering identify emerging patterns
- Products extracted from enriched case data, not search
""")

    # Cleanup
    try:
        Authentication.invalidate_token()
        print("\n✓ Token invalidated")
    except:
        pass

if __name__ == "__main__":
    main()
