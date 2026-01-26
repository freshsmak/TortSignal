# CDC WONDER API - Final Assessment
**Date**: 2026-01-26
**Status**: Extensive Testing Complete

---

## Investigation Summary

### User Guidance Received ✅
The user provided excellent information:
- CDC WONDER **does** have a public API for national-level data
- Uses XML-formatted requests via HTTP POST
- Endpoint: `https://wonder.cdc.gov/controller/datarequest/D76`
- Parameter conventions: B_ for grouping, M_ for measures, V_/F_ for filters, O_ for options
- Requires `accept_datause_restrictions=true`

### Attempts Made (12 Different Approaches)

1. ✅ **User-provided minimal XML template** - HTTP 500
2. ✅ **IBD-specific query (K50-K51)** - HTTP 500
3. ✅ **Ultra-minimal (deaths only, no filters)** - HTTP 500
4. ✅ **With F_D76.V5 age groups** - HTTP 500
5. ✅ **Explicit age group values (1-10)** - HTTP 500
6. ✅ **All filters = *All*** - HTTP 500
7. ✅ **Group by Year + Age (B_1 + B_2)** - HTTP 500
8. ✅ **Group by Year only, no filters** - HTTP 500
9. ✅ **No grouping, summarized data** - HTTP 500
10. ✅ **Session-based approach** - HTTP 400/500
11. ✅ **Form-based POST** - HTTP 400
12. ✅ **XML with corrected structure** - HTTP 500

---

## Consistent Error Pattern

**Every single request fails with**:
```
"To Group Results By 'Ten-Year Age Groups' you must also select
the 'Ten-Year Age Groups' button where found below section #1."
```

### Analysis of Error

1. **Language suggests web UI**: "button where found below section #1" refers to web form elements
2. **Hidden parameter**: There's likely an undocumented O_ option parameter that "enables" age grouping
3. **Database-specific**: D76 (Detailed Mortality) may have different requirements than documented
4. **API version mismatch**: Documentation may be outdated or for a different database

---

## What We Know Works

### ✅ Literature Fallback System
- Properly flags data as LOW confidence (0.50 vs 0.90)
- Cites peer-reviewed sources (Ye et al. 2020, Dahlhamer et al. 2016)
- Shows clear warnings: ⚠️ LOW CONFIDENCE (API unavailable)
- Scientifically defensible for preliminary risk assessment

### ✅ System Transparency
The system achieves its stated goal: **honesty about data quality**

---

## Recommended Next Steps

### Option 1: Accept Fallback ⭐ **RECOMMENDED**

**Reasoning**:
- System already transparent about data quality
- Literature sources are peer-reviewed
- Confidence penalty appropriately applied
- Meets core requirement: honest about limitations

**Timeline**: Immediate
**Risk**: Low (conservative approach)
**Effort**: None (already working)

---

### Option 2: Contact CDC WONDER Support

**Email**: wonder@cdc.gov

**Request**:
1. Current XML API documentation for D76 database
2. Example working XML query for mortality data by year
3. List of required O_ option parameters
4. Clarification on "Ten-Year Age Groups button" error

**Sample email**:
```
Subject: D76 Detailed Mortality API - XML Parameter Assistance

Hello CDC WONDER Support Team,

We're developing a public health research tool that queries mortality
trends for epidemiological analysis. We're attempting to use the D76
Detailed Mortality XML API but consistently receive this error:

"To Group Results By 'Ten-Year Age Groups' you must also select the
'Ten-Year Age Groups' button where found below section #1."

We've tried numerous parameter combinations including:
- B_1 (group by year), M_1 (deaths measure)
- F_D76.V5 with both *All* and explicit values
- B_2=D76.V5 (grouping by age)
- accept_datause_restrictions=true

Could you provide:
1. A working example XML query for deaths by year/ICD-10 code?
2. Documentation of required O_ option parameters?
3. The correct way to handle age group requirements?

Thank you for your assistance!
```

**Timeline**: 1-4 weeks for response
**Risk**: Medium (may not get response)
**Effort**: Low (just email)

---

### Option 3: Python Wrapper Libraries

User mentioned several packages:

#### `wonderapi` Package
```bash
pip install wonderapi
```

**Status**: ❌ Package not found in PyPI (as of test date)
- May be deprecated
- May be private/internal
- Name may have changed

#### `cdcwonderpy` Package
Mentioned for web UI automation (Selenium-based)

**Status**: Not tested yet
**Approach**: Automate the web browser interaction

**Try**:
```bash
pip install cdcwonderpy
# or search for similar packages:
pip search cdc wonder
```

**Timeline**: 1-2 days to test and integrate
**Risk**: Medium (may be fragile, requires maintenance)
**Effort**: Medium (testing, integration)

---

### Option 4: Manual Data Entry Tool

For high-priority chemicals requiring real CDC data:

```python
def import_cdc_wonder_csv(csv_file: str) -> DiseaseTrend:
    """
    Import manually downloaded CDC WONDER data

    Workflow:
    1. User visits CDC WONDER website
    2. Fills out form, downloads CSV
    3. Runs: python import_cdc_data.py chemical_name.csv
    4. Data imported with HIGH confidence flag
    """
    # Parse CSV
    # Create DiseaseTrend with confidence="HIGH"
    # Save to cache
```

**Timeline**: 1 day to implement
**Risk**: Low (users control data quality)
**Effort**: Low to medium (manual data collection)

---

### Option 5: Browser Automation (Last Resort)

Use Selenium/Playwright to automate the web form:

```python
from selenium import webdriver

def fetch_cdc_wonder_via_browser(icd_code, years):
    """Automate CDC WONDER web form"""
    driver = webdriver.Chrome()
    driver.get("https://wonder.cdc.gov/ucd-icd10.html")

    # Fill form
    # Click agree
    # Export data
    # Parse results

    return trend_data
```

**Timeline**: 2-3 days to implement reliably
**Risk**: High (fragile, CDC may block, requires maintenance)
**Effort**: High (complex setup, error handling)

---

## Comparison Matrix

| Option | Timeline | Risk | Effort | Data Quality | Maintenance |
|--------|----------|------|--------|--------------|-------------|
| **Accept Fallback** | Immediate | Low | None | LOW (0.50) | None |
| **Contact CDC** | 1-4 weeks | Medium | Low | HIGH (0.90) | Low |
| **Python Packages** | 1-2 days | Medium | Medium | HIGH (0.90) | Medium |
| **Manual Import** | 1 day | Low | Low-Med | HIGH (0.90) | Low |
| **Browser Automation** | 2-3 days | High | High | HIGH (0.90) | High |

---

## Our Recommendation: Hybrid Approach

### Phase 1: Accept Fallback (Immediate) ⭐
- System already works and is transparent
- Allows TortSignal to launch immediately
- Literature estimates are scientifically defensible

### Phase 2: Contact CDC (Parallel)
- Email wonder@cdc.gov for guidance
- If they provide working examples, update integration
- No risk, low effort

### Phase 3: Manual Import for Critical Cases (As Needed)
- Implement CSV import tool
- For high-priority litigation cases, manually download real CDC data
- Gives "escape hatch" for when real data is essential

---

## Files Created During Investigation

### Test Scripts
1. `debug_cdc_wonder.py` - Initial diagnostics
2. `test_cdc_wonder_fixed.py` - User-guided parameters
3. `test_cdc_wonder_simple.py` - Minimal requests
4. `test_cdc_wonder_session.py` - Session approach
5. `test_cdc_wonder_correct.py` - User's XML template
6. `test_cdc_wonder_ultra_simple.py` - Ultra-minimal
7. `test_cdc_wonder_with_age.py` - Age group filters
8. `test_cdc_wonder_group_by_age.py` - Age group grouping

### Verification
9. `verify_fallback_system.py` - Confirms transparency works

### Documentation
10. `CDC_WONDER_INVESTIGATION_RESULTS.md` - Technical details
11. `INVESTIGATION_SUMMARY.md` - Executive summary
12. `CDC_WONDER_FINAL_ASSESSMENT.md` - This document

---

## Conclusion

**We have made an exhaustive effort** to get CDC WONDER API working with:
- User-provided guidance
- 12 different parameter combinations
- Multiple approaches (XML, form, session)
- Extensive debugging and error analysis

**Result**: The API consistently rejects all requests with age group errors, suggesting undocumented or changed requirements.

**The system already works correctly** by:
- ✅ Falling back to literature estimates
- ✅ Flagging data as LOW confidence (0.50)
- ✅ Showing clear warnings to users
- ✅ Citing specific sources
- ✅ Being completely transparent about limitations

**Recommendation**:
1. ✅ **Accept the fallback** for now (meets goal of honesty)
2. 📧 **Email CDC WONDER support** for current API docs
3. 🔧 **Build manual import tool** for critical cases
4. ⏱️ **Revisit** when/if CDC provides working examples

The literature-based approach is scientifically sound for preliminary risk assessment, properly flagged, and allows TortSignal to launch immediately while maintaining its commitment to data quality transparency.

---

**Assessment by**: Claude
**Date**: 2026-01-26
**Recommendation**: Accept fallback + Contact CDC + Manual import tool
**Status**: Investigation Complete ✅
