#!/usr/bin/env python3
"""
Verify that CDC WONDER fallback system works properly with correct confidence tracking
"""

import sys
sys.path.insert(0, '/home/user/TortSignal/backend')

from integrations.cdc_wonder_enhanced import CDCWonderEnhancedAPI

def main():
    print("\n" + "="*80)
    print("VERIFY CDC WONDER FALLBACK SYSTEM")
    print("="*80)

    api = CDCWonderEnhancedAPI()

    print("\n📊 Testing IBD mortality trend (K50-K51)...")
    print("   This will attempt API access and fall back to literature estimates")
    print()

    trend = api.query_disease_trend(
        disease_icd10_code="K50-K51",
        start_year=1999,
        end_year=2020
    )

    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    print(f"\n✓ Disease: {trend.disease}")
    print(f"✓ Data Source: {trend.data_source}")
    print(f"✓ Confidence: {trend.confidence}")
    print(f"✓ Years of Data: {len(trend.years)}")
    print(f"✓ Trend Direction: {trend.trend_direction}")
    print(f"✓ Percent Change: {trend.percent_change:+.1f}%")

    if trend.years:
        print(f"\n📈 Trend Data:")
        print(f"   {trend.years[0]}: {trend.rates[0]:.2f} per 100k ({trend.counts[0]:,} deaths)")
        print(f"   {trend.years[-1]}: {trend.rates[-1]:.2f} per 100k ({trend.counts[-1]:,} deaths)")

    print(f"\n📝 Interpretation:")
    print(f"   {trend.interpretation}")

    print("\n" + "="*80)
    print("SYSTEM VERIFICATION")
    print("="*80)

    # Check that fallback is working correctly
    checks = {
        "Returns DiseaseTrend object": trend is not None,
        "Has confidence field": hasattr(trend, 'confidence'),
        "Confidence is LOW (fallback)": trend.confidence == "LOW",
        "Data source mentions literature": 'literature' in trend.data_source.lower(),
        "Has years of data": len(trend.years) > 0,
        "Has rate data": len(trend.rates) > 0,
        "Has count data": len(trend.counts) > 0,
        "Has interpretation": len(trend.interpretation) > 0,
        "Shows warning in data source": '⚠️' in trend.data_source or 'LOW' in trend.data_source,
    }

    all_pass = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"\n{status} {check}")
        if not result:
            all_pass = False

    print("\n" + "="*80)
    if all_pass:
        print("✅ SYSTEM VERIFIED: Fallback works correctly with proper confidence tracking")
        print("\n💡 Key Points:")
        print("   • CDC WONDER API failed (expected)")
        print("   • System fell back to literature estimates")
        print("   • Data is clearly flagged as LOW confidence")
        print("   • Users are transparently informed about data quality")
        print("\n✅ RECOMMENDATION: Accept the fallback approach")
    else:
        print("⚠️ ISSUES DETECTED: Some checks failed")
        return 1

    print("="*80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
