# UniCourt Connector Documentation

## Overview

The UniCourt connector provides access to federal and state court case data through the [UniCourt Enterprise API](https://unicourt.com/solutions/enterprise-api). It uses the official [UniCourt Python SDK](https://github.com/UniCourt/enterprise-api-py-sdk) to search for product liability cases.

**Purpose**: Detect early signals of emerging mass torts by monitoring new product liability filings across federal and state courts.

---

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# UniCourt API Credentials
UNICOURT_CLIENT_ID=your_client_id_here
UNICOURT_CLIENT_SECRET=your_client_secret_here
UNICOURT_BASE_URL=https://enterpriseapi.unicourt.com  # Optional - this is the default
```

### Getting Credentials

1. Sign up for a UniCourt Enterprise API account at https://unicourt.com/
2. Navigate to your account settings to find your Client ID and Client Secret
3. Pricing starts at $2,250/month (as of 2025)
4. Free trial may be available - contact sales@unicourt.com

---

## Installation

The connector requires the official UniCourt SDK:

```bash
# Install TortSignal with UniCourt support
pip install -e .

# Or install just the SDK
pip install unicourt
```

---

## Usage

### Basic Usage

```python
from src.connectors.unicourt import UniCourtConnector

# Initialize connector
connector = UniCourtConnector()

# Health check
if connector.health_check():
    print("✓ UniCourt API is accessible")

    # Fetch product liability cases from last 30 days
    for case in connector.fetch(days=30, limit=50):
        print(f"\nCase: {case.title}")
        print(f"  Filed: {case.filed_date}")
        print(f"  Defendant: {case.defendant_text}")
        print(f"  Plaintiff Firm: {case.plaintiff_firm}")
        print(f"  State: {case.state}")
```

### Integration with Discovery Pipeline

```python
from src.connectors.unicourt import UniCourtConnector
from src.pipeline.discovery import process_cases

connector = UniCourtConnector()
cases = list(connector.fetch(days=7, limit=100))

print(f"Found {len(cases)} new product liability cases")

# Feed into clustering/scoring pipeline
process_cases(cases)
```

### Command Line Testing

```bash
# Test health check
make health-check

# Fetch 5 recent cases
make test-unicourt

# Run full court discovery pipeline
make court-discovery

# Dry run (no database writes)
make court-discovery-dry
```

---

## API Details

### Search Query

The connector searches for cases with:
- **Case Type**: Product Liability
- **Filed Date**: Within specified number of days (default: 30)
- **Sorting**: Most recent first

### Query Structure

```
(CaseType:(caseTypeGroup:(Product Liability)) AND filedDate:[YYYY-MM-DD TO *])
```

### Pagination

- Default page size: 100 cases per request
- Maximum page size: 100 (API limit)
- Automatically fetches multiple pages up to specified limit

### Response Fields

The connector extracts:
- `case_id`: Unique case identifier
- `title`: Case name (e.g., "Smith v. Johnson & Johnson")
- `filed_date`: Date the case was filed
- `court`: Court information (name, jurisdiction, state)
- `parties`: Plaintiffs and defendants
- `attorneys`: Attorney and law firm information
- `url`: Link to case docket (if available)
- `complaint_snippet`: Excerpt from complaint (if available)

---

## Architecture

### Authentication Flow

1. Connector initializes with CLIENT_ID and CLIENT_SECRET from config
2. On first request, calls `Authentication.generate_new_token()`
3. SDK automatically includes token in all subsequent requests
4. Token is invalidated when connector is destroyed (via `__del__`)

**Note**: UniCourt maintains a maximum of 10 concurrent authentication tokens per account.

### Data Model

Cases are parsed into `CaseRecord` objects:

```python
@dataclass
class CaseRecord:
    source_uid: str           # UniCourt case ID
    title: str                # Case name
    filed_date: str | None    # Filing date (YYYY-MM-DD)
    jurisdiction: str         # "federal" or "state"
    state: str | None         # Two-letter state code
    plaintiff_firm: str | None # Primary plaintiff law firm
    url: str | None           # Docket URL
    complaint_snippet: str | None  # Complaint excerpt
    defendant_text: str | None     # Comma-separated defendants
    raw_data: dict            # Full API response
```

---

## Limitations

### Network Environment

The connector requires outbound HTTPS access to `enterpriseapi.unicourt.com`. In sandboxed or air-gapped environments, the connector will fail with DNS resolution errors.

**Workaround**: If testing in a restricted environment, the connector implementation can serve as a reference for when deployed to production.

### API Rate Limits

- Free tier: Unknown (contact UniCourt for details)
- Paid tier: Varies by plan
- Connector does not implement rate limiting - rely on SDK's built-in handling

### Coverage

- **Federal Courts**: Comprehensive coverage (PACER integration)
- **State Courts**: Coverage varies by jurisdiction
- **Nature of Suit Codes**: Searches for "Product Liability" case type group
  - This may include various NOS codes depending on court classification

### Not Yet Implemented

- `fetch_case_details()`: Fetch full docket for a specific case
  - Requires CaseAnalytics or CaseDocket SDK modules
  - See: https://docs.unicourt.com/
- **Court filtering**: Search specific courts or jurisdictions
- **Party name filtering**: Search by defendant or plaintiff name
- **Custom case types**: Currently hardcoded to Product Liability

---

## Troubleshooting

### "ImportError: UniCourt SDK is required but not installed"

**Solution**: Install the SDK:
```bash
pip install unicourt
```

### "HTTPSConnectionPool: Failed to resolve 'enterpriseapi.unicourt.com'"

**Cause**: DNS resolution failed - network connectivity issue or restricted environment

**Solutions**:
1. Check internet connectivity: `ping google.com`
2. Verify DNS resolution: `nslookup enterpriseapi.unicourt.com`
3. Check firewall/proxy settings
4. If in a sandboxed environment, connector won't work until deployed to production

### "Authentication failed with status 401"

**Cause**: Invalid CLIENT_ID or CLIENT_SECRET

**Solutions**:
1. Verify credentials in `.env` file
2. Check credentials in UniCourt account settings
3. Ensure no extra whitespace in credential values
4. Confirm account is active and not expired

### "Authentication failed with status 403"

**Cause**: Account may not have API access enabled

**Solution**: Contact UniCourt support to enable API access for your account

### Empty Results

**Possible causes**:
1. No product liability cases filed in the specified date range
2. Case type classification differs from "Product Liability"
3. API access limited to specific courts/jurisdictions

**Solutions**:
1. Increase date range: `connector.fetch(days=90)`
2. Check UniCourt web UI to verify data availability
3. Contact UniCourt support to verify account permissions

---

## Performance Considerations

### Batch Size

Default page size is 100 cases. For large datasets:

```python
# Fetch 500 cases in batches of 100
cases = list(connector.fetch(days=90, limit=500, page_size=100))
```

### Caching

The connector does not cache results. For repeated queries, cache results in your application layer:

```python
import functools

@functools.lru_cache(maxsize=10)
def get_recent_cases(days: int) -> list[CaseRecord]:
    connector = UniCourtConnector()
    return list(connector.fetch(days=days, limit=100))
```

### Connection Pooling

The SDK manages HTTP connections internally. Each connector instance maintains its own authentication token.

**Recommendation**: Create one connector instance per pipeline run, not per request.

---

## API Documentation

- **UniCourt API Docs**: https://docs.unicourt.com/
- **Python SDK**: https://github.com/UniCourt/enterprise-api-py-sdk
- **Use Case Examples**: https://github.com/UniCourt/enterprise-api-py-usecases
- **Product Page**: https://unicourt.com/solutions/enterprise-api

---

## Support

- **UniCourt Support**: support@unicourt.com
- **Sales Inquiries**: sales@unicourt.com
- **SDK Issues**: https://github.com/UniCourt/enterprise-api-py-sdk/issues

---

## Implementation Status

| Feature | Status | Notes |
|---------|--------|-------|
| Authentication | ✅ Complete | OAuth token generation via SDK |
| Health Check | ✅ Complete | Validates credentials |
| Case Search | ✅ Complete | Product liability cases by date |
| Field Extraction | ✅ Complete | Parties, attorneys, court info |
| Pagination | ✅ Complete | Automatic multi-page fetching |
| Error Handling | ✅ Complete | Logging and graceful failures |
| Case Details | ❌ Not Implemented | Requires additional SDK modules |
| Custom Filters | ❌ Not Implemented | Court, party name, case type filters |
| Webhooks | ❌ Not Implemented | Real-time case notifications |

---

## Example Output

```bash
$ make test-unicourt

Testing UniCourt connector (fetching 5 recent product liability cases)...
✓ UniCourt authentication successful

Fetching cases...
Found 5 cases:

1. Smith v. Johnson & Johnson
   Filed: 2025-01-15
   Defendant: Johnson & Johnson, Kenvue Inc.

2. Doe v. Abbott Laboratories
   Filed: 2025-01-12
   Defendant: Abbott Laboratories

3. Jones v. Bayer Healthcare
   Filed: 2025-01-10
   Defendant: Bayer Healthcare Pharmaceuticals Inc.

4. Williams v. Boston Scientific Corp
   Filed: 2025-01-08
   Defendant: Boston Scientific Corporation

5. Brown v. Medtronic Inc
   Filed: 2025-01-05
   Defendant: Medtronic, Inc.
```

---

## Version History

- **v1.0** (2025-01): Initial implementation using UniCourt SDK
  - Product liability case search
  - OAuth authentication
  - Basic field extraction
  - Health check endpoint

---

## License

Part of the TortSignal project. See main project LICENSE file.
