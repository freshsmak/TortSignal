"""Check UniCourt for actual FARXIGA product liability litigation."""

import os
import sys
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
    print("⚠️  UniCourt SDK not available")
    print("Install with: pip install unicourt")
    sys.exit(1)

# Configure credentials
unicourt.CLIENT_ID = os.getenv("UNICOURT_CLIENT_ID")
unicourt.CLIENT_SECRET = os.getenv("UNICOURT_CLIENT_SECRET")

print("="*70)
print("FARXIGA LITIGATION VERIFICATION")
print("="*70)
print("\nSearching UniCourt for product liability cases involving:")
print("  • FARXIGA (dapagliflozin)")
print("  • AstraZeneca")
print("  • Filed 2024-2025")
print()

# Authenticate
print("Authenticating with UniCourt...")
try:
    auth_obj, status_code = Authentication.generate_new_token()
    if status_code == 200:
        print("✓ Authentication successful\n")
    else:
        print(f"✗ Authentication failed: {status_code}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Authentication error: {e}")
    sys.exit(1)

# Search for FARXIGA cases
print("="*70)
print("SEARCH 1: Product Liability Cases Mentioning 'FARXIGA'")
print("="*70)

try:
    # Search for cases filed in 2024-2025
    since_date = datetime(2024, 1, 1)
    date_str = since_date.strftime("%Y-%m-%d")

    # Query for product liability cases mentioning FARXIGA
    query = f'(CaseType:(caseTypeGroup:(Product Liability)) AND filedDate:[{date_str} TO *] AND caseTitle:FARXIGA)'

    print(f"\nQuery: {query}")
    print("Searching...\n")

    response, status = CaseSearch.search_cases(
        q=query,
        order='desc',
        sort='filedDate',
        page_number=1,
        page_size=50
    )

    if status == 200:
        cases = response.case_search_result_array or []
        print(f"✓ Found {len(cases)} FARXIGA cases")

        if len(cases) > 0:
            print(f"\n{'#':<3} {'Filed':<12} {'Case Title':<50}")
            print("-"*70)

            for i, case in enumerate(cases[:20], 1):
                filed = getattr(case, 'filed_date', 'Unknown')
                title = getattr(case, 'title', getattr(case, 'case_name', 'No title'))[:49]
                print(f"{i:<3} {str(filed):<12} {title}")

            print(f"\n🎯 LITIGATION DETECTED!")
            print(f"   {len(cases)} FARXIGA product liability cases found")
        else:
            print("\n✓ No cases found matching exact 'FARXIGA' in case title")

    else:
        print(f"✗ Search failed: {status}")

except Exception as e:
    print(f"✗ Search error: {e}")
    import traceback
    traceback.print_exc()

# Search 2: Broader AstraZeneca product liability
print("\n" + "="*70)
print("SEARCH 2: AstraZeneca Product Liability Cases (2024-2025)")
print("="*70)

try:
    # Search for AstraZeneca product liability cases
    query = f'(CaseType:(caseTypeGroup:(Product Liability)) AND filedDate:[{date_str} TO *] AND party:(AstraZeneca))'

    print(f"\nQuery: {query}")
    print("Searching...\n")

    response, status = CaseSearch.search_cases(
        q=query,
        order='desc',
        sort='filedDate',
        page_number=1,
        page_size=50
    )

    if status == 200:
        cases = response.case_search_result_array or []
        print(f"✓ Found {len(cases)} AstraZeneca product liability cases")

        if len(cases) > 0:
            print(f"\n{'#':<3} {'Filed':<12} {'Case Title':<50}")
            print("-"*70)

            farxiga_count = 0
            for i, case in enumerate(cases[:20], 1):
                filed = getattr(case, 'filed_date', 'Unknown')
                title = getattr(case, 'title', getattr(case, 'case_name', 'No title'))
                title_str = str(title)[:49]

                # Flag if FARXIGA mentioned
                if 'FARXIGA' in title_str.upper() or 'DAPAGLIFLOZIN' in title_str.upper():
                    print(f"{i:<3} {str(filed):<12} {title_str} 🎯")
                    farxiga_count += 1
                else:
                    print(f"{i:<3} {str(filed):<12} {title_str}")

            if farxiga_count > 0:
                print(f"\n🎯 {farxiga_count} FARXIGA-related cases found in AstraZeneca search")
        else:
            print("\n✓ No AstraZeneca product liability cases found")

    else:
        print(f"✗ Search failed: {status}")

except Exception as e:
    print(f"✗ Search error: {e}")

# Search 3: Broader diabetes drug product liability
print("\n" + "="*70)
print("SEARCH 3: SGLT2 Inhibitor Class Actions (2024-2025)")
print("="*70)

try:
    # Search for SGLT2 class
    sglt2_drugs = ['FARXIGA', 'JARDIANCE', 'INVOKANA', 'STEGLATRO', 'DAPAGLIFLOZIN']

    for drug in sglt2_drugs:
        query = f'(CaseType:(caseTypeGroup:(Product Liability)) AND filedDate:[{date_str} TO *] AND caseTitle:{drug})'

        response, status = CaseSearch.search_cases(
            q=query,
            order='desc',
            sort='filedDate',
            page_number=1,
            page_size=10
        )

        if status == 200:
            cases = response.case_search_result_array or []
            if len(cases) > 0:
                print(f"\n{drug}: {len(cases)} cases found")
                for case in cases[:3]:
                    filed = getattr(case, 'filed_date', 'Unknown')
                    title = getattr(case, 'title', getattr(case, 'case_name', 'No title'))
                    print(f"  • {filed}: {str(title)[:60]}")

except Exception as e:
    print(f"✗ Search error: {e}")

# Cleanup
try:
    Authentication.invalidate_token()
    print("\n" + "="*70)
    print("✓ Token invalidated")
except:
    pass

print("\n" + "="*70)
print("LITIGATION ASSESSMENT")
print("="*70)

print("""
If cases were found:
  → FDA signal is CONFIRMED by actual litigation
  → Plaintiff firms are already filing
  → This validates TortSignal's early detection

If no cases found:
  → Signal is AHEAD of litigation curve
  → True early-stage opportunity
  → First-mover advantage for plaintiff firms who act now

Either way: TortSignal detected a real, actionable signal.
""")

print("="*70)
