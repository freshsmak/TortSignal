"""
Test UniCourt API using the official Python SDK.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize credentials
import unicourt
from unicourt import Authentication, CaseSearch

unicourt.CLIENT_ID = os.getenv("UNICOURT_CLIENT_ID")
unicourt.CLIENT_SECRET = os.getenv("UNICOURT_CLIENT_SECRET")

print("="*60)
print("UniCourt API Test using Official SDK")
print("="*60)
print(f"Client ID: {unicourt.CLIENT_ID[:10]}...")
print(f"Client Secret: {unicourt.CLIENT_SECRET[:10]}...")
print()

# Test 1: Authentication
print("\n" + "="*60)
print("Test 1: Authentication")
print("="*60)

try:
    auth_obj, status_code = Authentication.generate_new_token()
    print(f"✓ Authentication successful! Status: {status_code}")
    print(f"Token type: {type(auth_obj)}")
except Exception as e:
    print(f"✗ Authentication failed: {e}")
    sys.exit(1)

# Test 2: Search Product Liability Cases
print("\n" + "="*60)
print("Test 2: Search Product Liability Cases")
print("="*60)

try:
    # Search for product liability cases filed in the last 90 days
    since_date = datetime.now() - timedelta(days=90)
    date_str = since_date.strftime("%Y-%m-%d")

    query = f'(CaseType:(caseTypeGroup:(Product Liability)) AND filedDate:[{date_str} TO *])'

    print(f"Query: {query}")
    print("Executing search...")

    response, status = CaseSearch.search_cases(
        q=query,
        order='desc',
        sort='filedDate',
        page_number=1
    )

    print(f"✓ Search successful! Status: {status}")
    print(f"Response type: {type(response)}")

    # Print response attributes
    if hasattr(response, '__dict__'):
        print(f"\nResponse attributes: {list(response.__dict__.keys())}")

    # Try to access results
    if hasattr(response, 'case_search_result_array'):
        cases = response.case_search_result_array
        print(f"\nFound {len(cases)} cases")

        if len(cases) > 0:
            print("\nFirst case details:")
            first_case = cases[0]
            if hasattr(first_case, '__dict__'):
                for key, value in first_case.__dict__.items():
                    if value is not None and key not in ['_data_store', '_check_type']:
                        print(f"  {key}: {value}")

    # Also try total_count if available
    if hasattr(response, 'total_count'):
        print(f"\nTotal matching cases: {response.total_count}")

except Exception as e:
    print(f"✗ Search failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Recent Cases (simpler query)
print("\n" + "="*60)
print("Test 3: Recent Cases (Any Type)")
print("="*60)

try:
    # Just get recent cases without filtering by type
    since_date = datetime.now() - timedelta(days=30)
    date_str = since_date.strftime("%Y-%m-%d")

    query = f'filedDate:[{date_str} TO *]'

    print(f"Query: {query}")
    print("Executing search...")

    response, status = CaseSearch.search_cases(
        q=query,
        order='desc',
        sort='filedDate',
        page_number=1,
        page_size=5  # Just get a few results
    )

    print(f"✓ Search successful! Status: {status}")

    if hasattr(response, 'case_search_result_array'):
        cases = response.case_search_result_array
        print(f"Found {len(cases)} recent cases")

        for i, case in enumerate(cases[:3]):
            print(f"\nCase {i+1}:")
            if hasattr(case, 'title'):
                print(f"  Title: {case.title}")
            if hasattr(case, 'case_number'):
                print(f"  Case #: {case.case_number}")
            if hasattr(case, 'filed_date'):
                print(f"  Filed: {case.filed_date}")
            if hasattr(case, 'court'):
                print(f"  Court: {case.court}")

except Exception as e:
    print(f"✗ Search failed: {e}")
    import traceback
    traceback.print_exc()

# Cleanup
print("\n" + "="*60)
print("Cleaning up...")
print("="*60)

try:
    Authentication.invalidate_token()
    print("✓ Token invalidated")
except Exception as e:
    print(f"Note: {e}")

print("\nTest complete!")
