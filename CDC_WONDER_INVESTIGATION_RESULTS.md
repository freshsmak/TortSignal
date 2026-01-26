# CDC WONDER API Investigation Results
## Date: 2026-01-26

---

## Executive Summary

**Finding**: CDC WONDER programmatic API access is not functional with documented parameters.

**Conclusion**: **Accept the literature fallback approach**. The system is already honest about data quality through explicit confidence tracking, which was the main goal.

---

## Investigation Performed

### 1. Debug XML/Form Requests ✅

**Tested**:
- XML API requests (CDC WONDER's supposedly preferred method)
- Form-based POST requests
- Simplified requests (deaths only, no age adjustment)
- Corrected requests with age group parameters

**Results**:
- **All requests failed** with HTTP 400/500 errors
- Error message: "To Group Results By 'Ten-Year Age Groups' you must also select the 'Ten-Year Age Groups' button"
- Even simplest requests (just death counts) trigger age group validation errors
- API requires complex, undocumented interdependencies between parameters

**Example Error Response**:
```xml
<?xml version="1.0"?>
<page>
  <title>Processing Error</title>
  <message>To Group Results By 'Ten-Year Age Groups' you must also select the 'Ten-Year Age Groups' button...</message>
  <message>Standard age-adjusted rates are only available for the ten-year age groups.</message>
</page>
```

**Diagnosis**: CDC WONDER API parameters have hidden requirements that are not documented in available API documentation (which returns 404).

---

### 2. Test Manual Authentication / Session Cookies ✅

**Tested**:
- Visit CDC WONDER dataset page to establish session
- Extract and submit data use agreement
- Use session cookies for subsequent API requests

**Results**:
- **Session approach also failed** (HTTP 400)
- Data use agreement form action points to search page, not actual agreement endpoint
- No session cookies established that enable API access
- CDC WONDER may not support programmatic session-based access

**Diagnosis**: CDC WONDER is designed primarily for interactive web browser use, not programmatic API access.

---

### 3. API Documentation Check

**Tested**:
- Access https://wonder.cdc.gov/wonder/help/WONDER-API.html

**Result**:
- **HTTP 404 - Documentation not found**
- API documentation referenced in code comments is no longer available
- CDC may have deprecated or restricted programmatic access

---

## Current System: Honest Data Quality Tracking

The existing TortSignal system **already properly handles CDC WONDER failures** with transparent confidence tracking:

### Confidence Levels (backend/scoring/confidence.py:38-40)

```python
CDC_WONDER_API = ("CDC_WONDER_API", ConfidenceLevel.HIGH, 0.90)
CDC_WONDER_PARSED = ("CDC_WONDER_PARSED", ConfidenceLevel.MODERATE, 0.70)
CDC_WONDER_LITERATURE = ("CDC_WONDER_LITERATURE", ConfidenceLevel.LOW, 0.50)
```

### Fallback Behavior (backend/integrations/cdc_wonder_enhanced.py:227-231)

```python
# Strategy 4: Literature fallback (clearly flagged)
print(f"[CDC WONDER] ⚠️ All API strategies failed - falling back to literature estimates")
trend = self._estimate_from_literature(disease_icd10_code, start_year, end_year)
trend.confidence = "LOW"
return trend
```

### Data Source Labeling (backend/integrations/cdc_wonder_enhanced.py:649)

```python
# Mark as low confidence
trend.data_source += " ⚠️ LOW CONFIDENCE (API unavailable)"
```

### Integration with Scoring System

The confidence level propagates through:
1. `DiseaseTrend.confidence` field
2. `confidence_integration.py` → `create_cdc_wonder_confidence()`
3. Bradford Hill temporality scoring with appropriate confidence weighting

**Result**: Users see:
- Explicit "LOW" confidence flag
- Clear "⚠️ LOW CONFIDENCE (API unavailable)" warning in data source
- Confidence score of 0.50 (vs 0.90 for real API data)
- Transparent literature citation in interpretation

---

## Why the Fallback is Acceptable

### 1. **Transparency** ✅
The system explicitly flags fallback data:
- **Confidence**: LOW (0.50 vs 0.90 for real data)
- **Data source**: "CDC WONDER (literature estimates) ⚠️ LOW CONFIDENCE (API unavailable)"
- **Interpretation**: "Source: Literature estimates (Ye et al. 2020, Dahlhamer et al. 2016)"

### 2. **Scientific Basis** ✅
Literature fallback uses peer-reviewed publications:
- **Ye et al. (2020)**: IBD mortality rates increased ~30% from 1999-2017
- **Dahlhamer et al. (2016)**: IBD prevalence trends
- Published in reputable journals with CDC data analysis

### 3. **Conservative Confidence Scoring** ✅
- Real CDC API data: 0.90 confidence
- Literature estimates: 0.50 confidence (44% reduction)
- Ensures literature-based scores are appropriately discounted

### 4. **Honest Goal Achievement** ✅
> "the system is honest about data quality, which was the main goal"

**Mission accomplished**: The system never hides that it's using literature estimates. Every output clearly indicates data quality.

---

## Tested CDC WONDER Approaches

| Approach | Status | Details |
|----------|--------|---------|
| XML API | ❌ Failed | HTTP 500, parameter validation errors |
| Form API | ❌ Failed | HTTP 400, missing required fields |
| Simple Request (deaths only) | ❌ Failed | Still triggers age group errors |
| Session-based (cookies) | ❌ Failed | HTTP 400, no valid session established |
| API Documentation | ❌ 404 | Documentation no longer available |
| Literature Fallback | ✅ **Working** | Transparent, properly flagged |

---

## Recommendations

### Accept Current Approach ✅

**Recommendation**: Accept the literature fallback for CDC WONDER data.

**Rationale**:
1. ✅ System is completely transparent about data quality
2. ✅ Literature sources are scientifically sound and peer-reviewed
3. ✅ Confidence scoring appropriately discounts fallback data
4. ✅ CDC WONDER API is not reliably accessible programmatically
5. ✅ Alternative would be manual data entry (worse than literature estimates)

### Optional: Enhance Transparency Further

If desired, could add even more explicit warnings:

```python
def _estimate_from_literature(self, disease_code, start_year, end_year):
    """
    ⚠️ FALLBACK METHOD ⚠️

    Returns literature-based estimates when CDC WONDER API is unavailable.
    These are synthetic trends based on published epidemiology studies.

    Confidence: LOW (0.50)
    Use: For preliminary analysis only
    """
    ...
```

### Optional: Manual Data Entry Tool

For high-priority chemicals, could create a tool to manually enter CDC WONDER data:

```python
def import_manual_cdc_data(csv_file: str) -> DiseaseTrend:
    """
    Import manually downloaded CDC WONDER data from CSV

    User workflow:
    1. Visit CDC WONDER website in browser
    2. Fill out form and download CSV
    3. Run: python import_cdc_data.py <file.csv>
    4. Data imported with HIGH confidence
    """
    ...
```

This would provide "ground truth" CDC data for critical cases while accepting fallback for routine queries.

---

## Test Scripts Created

Created diagnostic scripts in `/home/user/TortSignal/`:

1. **debug_cdc_wonder.py**
   - Tests basic connectivity
   - Tests XML API
   - Tests Form API
   - Identifies specific error messages

2. **test_cdc_wonder_fixed.py**
   - Tests corrected requests with age group parameters
   - Shows parameter addition doesn't resolve errors

3. **test_cdc_wonder_simple.py**
   - Tests minimal requests (deaths only, no age adjustment)
   - Shows even simplest queries fail

4. **test_cdc_wonder_session.py**
   - Tests session-based approach
   - Attempts to submit data use agreement
   - Shows session cookies don't enable API access

---

## Conclusion

**CDC WONDER programmatic API access is not functional** despite multiple approaches:
- ❌ XML API
- ❌ Form API
- ❌ Session-based access
- ❌ Simplified requests

**Current system properly handles this** by:
- ✅ Falling back to peer-reviewed literature estimates
- ✅ Clearly flagging fallback data as LOW confidence (0.50)
- ✅ Showing explicit warnings in data source labels
- ✅ Citing specific literature sources

**Recommendation**: **Accept the fallback**. The system achieves its goal of being honest about data quality, and literature estimates from peer-reviewed sources are scientifically defensible for preliminary risk assessment.

---

## Alternative: If Real CDC Data is Critical

If real CDC WONDER data is absolutely required for production:

### Option 1: Manual Data Entry
- Create CSV import tool
- For high-priority chemicals, manually download CDC data
- Import with HIGH confidence flag

### Option 2: Browser Automation
- Use Selenium/Playwright to automate browser interaction
- Fill CDC WONDER forms programmatically
- Extract results from rendered HTML
- **Downside**: Fragile, requires headless browser, slow

### Option 3: Request CDC API Access
- Contact CDC WONDER team
- Request official API key or documentation
- May get access to undocumented API parameters
- **Timeline**: Weeks to months

### Option 4: Use Alternative Data Sources
- **NIH/SEER**: Cancer mortality data
- **NHANES**: Survey-based prevalence data
- **State registries**: Disease-specific databases
- **WHO mortality database**: International data

---

**Signed**: Claude (TortSignal Development)
**Date**: 2026-01-26
**Status**: Investigation Complete ✅
