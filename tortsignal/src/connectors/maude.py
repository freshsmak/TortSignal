"""FDA MAUDE (device adverse events) connector with broad discovery capabilities."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Generator

import requests

from src.connectors.base import BaseConnector
from src.models import MAUDEReport, DeviceTrend, DeviceCategoryTrend, ManufacturerTrend

logger = logging.getLogger(__name__)

MAUDE_BASE_URL = "https://api.fda.gov/device/event.json"


class MAUDEConnector(BaseConnector):
    """
    Connector for FDA MAUDE device adverse event data via OpenFDA API.
    
    Supports multiple discovery paradigms:
    1. Device-first: "Is device X showing elevated adverse events?"
    2. Category-first: "Are whole classes of devices failing?" (by product code)
    3. Manufacturer-first: "Is a company having systemic quality issues?"
    4. Problem-first: "What device problems are spiking?"
    
    Category-first discovery is especially powerful for devices because
    the FDA uses product codes to classify device types. A spike in
    "OTN" (surgical mesh) catches ALL mesh products across manufacturers.
    """

    def __init__(self, api_key: str | None = None, reference_date: datetime | None = None):
        self.api_key = api_key
        self.reference_date = reference_date or self.reference_date
        self.session = requests.Session()
        if api_key:
            self.session.params = {"api_key": api_key}

    @property
    def source_name(self) -> str:
        return "maude"

    def health_check(self) -> bool:
        try:
            response = self.session.get(MAUDE_BASE_URL, params={"limit": 1}, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"MAUDE health check failed: {e}")
            return False

    # =========================================================================
    # CORE FETCH METHODS
    # =========================================================================

    def fetch(
        self,
        device_name: str | None = None,
        product_code: str | None = None,
        manufacturer: str | None = None,
        days: int = 180,
        limit: int = 100,
    ) -> Generator[MAUDEReport, None, None]:
        """Fetch MAUDE reports with flexible filtering."""
        end_date = self.reference_date
        start_date = end_date - timedelta(days=days)
        date_range = f"[{start_date.strftime('%Y-%m-%d')}+TO+{end_date.strftime('%Y-%m-%d')}]"

        search_parts = [f"date_received:{date_range}"]
        if device_name:
            search_parts.append(f'device.brand_name:"{device_name}"')
        if product_code:
            search_parts.append(f'device.device_report_product_code:"{product_code}"')
        if manufacturer:
            search_parts.append(f'device.manufacturer_d_name:"{manufacturer}"')

        search = "+AND+".join(search_parts)

        skip = 0
        fetched = 0
        while fetched < limit:
            batch_limit = min(100, limit - fetched)
            try:
                response = self.session.get(
                    MAUDE_BASE_URL,
                    params={"search": search, "limit": batch_limit, "skip": skip},
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    break
                raise

            results = data.get("results", [])
            if not results:
                break

            for item in results:
                yield self._parse_report(item)
                fetched += 1

            skip += len(results)
            if len(results) < batch_limit:
                break

    def _parse_report(self, raw: dict[str, Any]) -> MAUDEReport:
        devices = raw.get("device", [{}])
        device = devices[0] if devices else {}
        patient = raw.get("patient", [{}])
        patient = patient[0] if patient else {}

        return MAUDEReport(
            mdr_report_key=str(raw.get("mdr_report_key", "")),
            event_type=raw.get("event_type", ""),
            report_date=raw.get("date_received", ""),
            manufacturer=device.get("manufacturer_d_name"),
            brand_name=device.get("brand_name"),
            device_problem_codes=device.get("device_problem_codes", []),
            event_description=raw.get("mdr_text", [{}])[0].get("text") if raw.get("mdr_text") else None,
            patient_sex=patient.get("patient_sex"),
            patient_age=patient.get("patient_age"),
        )

    # =========================================================================
    # DEVICE-FIRST DISCOVERY (Traditional approach)
    # =========================================================================

    def get_trending_devices(
        self, days: int = 30, top_n: int = 200
    ) -> list[dict[str, Any]]:
        """Get top devices by adverse event count."""
        end_date = self.reference_date
        start_date = end_date - timedelta(days=days)
        date_range = f"[{start_date.strftime('%Y-%m-%d')}+TO+{end_date.strftime('%Y-%m-%d')}]"

        try:
            response = self.session.get(
                MAUDE_BASE_URL,
                params={
                    "search": f"date_received:{date_range}",
                    "count": "device.brand_name.exact",
                    "limit": min(top_n, 1000),
                },
                timeout=30,
            )
            response.raise_for_status()
            return [{"device_name": item["term"], "count": item["count"]} for item in response.json().get("results", [])]
        except Exception as e:
            logger.error(f"Failed to get trending devices: {e}")
            return []

    def get_device_trend(
        self, device_name: str, current_days: int = 30, baseline_days: int = 365
    ) -> DeviceTrend | None:
        """Calculate adverse event trend for a specific device."""
        now = self.reference_date

        current_start = now - timedelta(days=current_days)
        current_count = self._count_reports_for_device(device_name, current_start, now)

        baseline_end = now - timedelta(days=baseline_days)
        baseline_start = baseline_end - timedelta(days=current_days)
        baseline_count = self._count_reports_for_device(device_name, baseline_start, baseline_end)

        if baseline_count == 0:
            delta_pct = float("inf") if current_count > 0 else 0.0
        else:
            delta_pct = ((current_count - baseline_count) / baseline_count) * 100

        top_problems = self._get_top_problems_for_device(device_name, current_start, now)
        manufacturer = self._get_manufacturer_for_device(device_name, current_start, now)

        return DeviceTrend(
            source="maude",
            device_name=device_name,
            product_code=None,
            manufacturer=manufacturer,
            window_days=current_days,
            reports_current=current_count,
            reports_baseline=baseline_count,
            delta_pct=delta_pct,
            top_problems=top_problems,
        )

    def _count_reports_for_device(self, device_name: str, start: datetime, end: datetime) -> int:
        date_range = f"[{start.strftime('%Y-%m-%d')}+TO+{end.strftime('%Y-%m-%d')}]"
        search = f'date_received:{date_range}+AND+device.brand_name:"{device_name}"'
        try:
            response = self.session.get(MAUDE_BASE_URL, params={"search": search, "limit": 1}, timeout=30)
            if response.status_code == 404:
                return 0
            response.raise_for_status()
            return response.json().get("meta", {}).get("results", {}).get("total", 0)
        except Exception as e:
            logger.error(f"Failed to count reports for {device_name}: {e}")
            return 0

    def _get_top_problems_for_device(self, device_name: str, start: datetime, end: datetime, top_n: int = 10) -> list[str]:
        date_range = f"[{start.strftime('%Y-%m-%d')}+TO+{end.strftime('%Y-%m-%d')}]"
        search = f'date_received:{date_range}+AND+device.brand_name:"{device_name}"'
        try:
            response = self.session.get(
                MAUDE_BASE_URL,
                params={"search": search, "count": "device.openfda.device_name.exact", "limit": top_n},
                timeout=30,
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            return [item["term"] for item in response.json().get("results", [])]
        except Exception as e:
            logger.error(f"Failed to get problems for {device_name}: {e}")
            return []

    def _get_manufacturer_for_device(self, device_name: str, start: datetime, end: datetime) -> str | None:
        date_range = f"[{start.strftime('%Y-%m-%d')}+TO+{end.strftime('%Y-%m-%d')}]"
        search = f'date_received:{date_range}+AND+device.brand_name:"{device_name}"'
        try:
            response = self.session.get(
                MAUDE_BASE_URL,
                params={"search": search, "count": "device.manufacturer_d_name.exact", "limit": 1},
                timeout=30,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            results = response.json().get("results", [])
            return results[0]["term"] if results else None
        except Exception:
            return None

    # =========================================================================
    # CATEGORY-FIRST DISCOVERY (Key innovation for devices)
    # =========================================================================

    def get_trending_product_codes(
        self, days: int = 30, top_n: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get top device product codes by adverse event count.
        
        This catches WHOLE CATEGORIES of devices, not just individual brands.
        Example: Product code "OTN" = all surgical mesh products
        """
        end_date = self.reference_date
        start_date = end_date - timedelta(days=days)
        date_range = f"[{start_date.strftime('%Y-%m-%d')}+TO+{end_date.strftime('%Y-%m-%d')}]"

        try:
            response = self.session.get(
                MAUDE_BASE_URL,
                params={
                    "search": f"date_received:{date_range}",
                    "count": "device.device_report_product_code.exact",
                    "limit": min(top_n, 1000),
                },
                timeout=30,
            )
            response.raise_for_status()
            return [{"product_code": item["term"], "count": item["count"]} for item in response.json().get("results", [])]
        except Exception as e:
            logger.error(f"Failed to get trending product codes: {e}")
            return []

    def get_category_trend(
        self, product_code: str, current_days: int = 30, baseline_days: int = 365
    ) -> DeviceCategoryTrend | None:
        """
        Calculate trend for a device category (by product code).
        Returns the category trend with top manufacturers and brands (trace-back).
        """
        now = self.reference_date

        current_start = now - timedelta(days=current_days)
        current_count = self._count_reports_for_code(product_code, current_start, now)

        baseline_end = now - timedelta(days=baseline_days)
        baseline_start = baseline_end - timedelta(days=current_days)
        baseline_count = self._count_reports_for_code(product_code, baseline_start, baseline_end)

        if baseline_count == 0:
            delta_pct = float("inf") if current_count > 0 else 0.0
        else:
            delta_pct = ((current_count - baseline_count) / baseline_count) * 100

        top_manufacturers = self._get_top_manufacturers_for_code(product_code, current_start, now)
        top_brands = self._get_top_brands_for_code(product_code, current_start, now)

        return DeviceCategoryTrend(
            source="maude",
            product_code=product_code,
            product_code_name=None,  # Would need a lookup table
            window_days=current_days,
            reports_current=current_count,
            reports_baseline=baseline_count,
            delta_pct=delta_pct,
            top_manufacturers=top_manufacturers,
            top_brands=top_brands,
        )

    def _count_reports_for_code(self, product_code: str, start: datetime, end: datetime) -> int:
        date_range = f"[{start.strftime('%Y-%m-%d')}+TO+{end.strftime('%Y-%m-%d')}]"
        search = f'date_received:{date_range}+AND+device.device_report_product_code:"{product_code}"'
        try:
            response = self.session.get(MAUDE_BASE_URL, params={"search": search, "limit": 1}, timeout=30)
            if response.status_code == 404:
                return 0
            response.raise_for_status()
            return response.json().get("meta", {}).get("results", {}).get("total", 0)
        except Exception as e:
            logger.error(f"Failed to count reports for code {product_code}: {e}")
            return 0

    def _get_top_manufacturers_for_code(self, product_code: str, start: datetime, end: datetime, top_n: int = 20) -> list[dict[str, Any]]:
        date_range = f"[{start.strftime('%Y-%m-%d')}+TO+{end.strftime('%Y-%m-%d')}]"
        search = f'date_received:{date_range}+AND+device.device_report_product_code:"{product_code}"'
        try:
            response = self.session.get(
                MAUDE_BASE_URL,
                params={"search": search, "count": "device.manufacturer_d_name.exact", "limit": top_n},
                timeout=30,
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            return [{"manufacturer": item["term"], "count": item["count"]} for item in response.json().get("results", [])]
        except Exception as e:
            logger.error(f"Failed to get manufacturers for code {product_code}: {e}")
            return []

    def _get_top_brands_for_code(self, product_code: str, start: datetime, end: datetime, top_n: int = 20) -> list[dict[str, Any]]:
        date_range = f"[{start.strftime('%Y-%m-%d')}+TO+{end.strftime('%Y-%m-%d')}]"
        search = f'date_received:{date_range}+AND+device.device_report_product_code:"{product_code}"'
        try:
            response = self.session.get(
                MAUDE_BASE_URL,
                params={"search": search, "count": "device.brand_name.exact", "limit": top_n},
                timeout=30,
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            return [{"brand_name": item["term"], "count": item["count"]} for item in response.json().get("results", [])]
        except Exception as e:
            logger.error(f"Failed to get brands for code {product_code}: {e}")
            return []

    # =========================================================================
    # MANUFACTURER-FIRST DISCOVERY
    # =========================================================================

    def get_trending_manufacturers(
        self, days: int = 30, top_n: int = 100
    ) -> list[dict[str, Any]]:
        """Get manufacturers by total adverse event count (detect systemic QC issues)."""
        end_date = self.reference_date
        start_date = end_date - timedelta(days=days)
        date_range = f"[{start_date.strftime('%Y-%m-%d')}+TO+{end_date.strftime('%Y-%m-%d')}]"

        try:
            response = self.session.get(
                MAUDE_BASE_URL,
                params={
                    "search": f"date_received:{date_range}",
                    "count": "device.manufacturer_d_name.exact",
                    "limit": min(top_n, 1000),
                },
                timeout=30,
            )
            response.raise_for_status()
            return [{"manufacturer": item["term"], "count": item["count"]} for item in response.json().get("results", [])]
        except Exception as e:
            logger.error(f"Failed to get trending manufacturers: {e}")
            return []

    def get_manufacturer_trend(
        self, manufacturer: str, current_days: int = 30, baseline_days: int = 365
    ) -> ManufacturerTrend | None:
        """Calculate trend for a specific manufacturer across all their devices."""
        now = self.reference_date

        current_start = now - timedelta(days=current_days)
        current_count = self._count_reports_for_manufacturer(manufacturer, current_start, now)

        baseline_end = now - timedelta(days=baseline_days)
        baseline_start = baseline_end - timedelta(days=current_days)
        baseline_count = self._count_reports_for_manufacturer(manufacturer, baseline_start, baseline_end)

        if baseline_count == 0:
            delta_pct = float("inf") if current_count > 0 else 0.0
        else:
            delta_pct = ((current_count - baseline_count) / baseline_count) * 100

        top_products = self._get_top_products_for_manufacturer(manufacturer, current_start, now)

        return ManufacturerTrend(
            source="maude",
            manufacturer=manufacturer,
            window_days=current_days,
            reports_current=current_count,
            reports_baseline=baseline_count,
            delta_pct=delta_pct,
            top_products=top_products,
        )

    def _count_reports_for_manufacturer(self, manufacturer: str, start: datetime, end: datetime) -> int:
        date_range = f"[{start.strftime('%Y-%m-%d')}+TO+{end.strftime('%Y-%m-%d')}]"
        search = f'date_received:{date_range}+AND+device.manufacturer_d_name:"{manufacturer}"'
        try:
            response = self.session.get(MAUDE_BASE_URL, params={"search": search, "limit": 1}, timeout=30)
            if response.status_code == 404:
                return 0
            response.raise_for_status()
            return response.json().get("meta", {}).get("results", {}).get("total", 0)
        except Exception as e:
            logger.error(f"Failed to count reports for manufacturer {manufacturer}: {e}")
            return 0

    def _get_top_products_for_manufacturer(self, manufacturer: str, start: datetime, end: datetime, top_n: int = 20) -> list[dict[str, Any]]:
        date_range = f"[{start.strftime('%Y-%m-%d')}+TO+{end.strftime('%Y-%m-%d')}]"
        search = f'date_received:{date_range}+AND+device.manufacturer_d_name:"{manufacturer}"'
        try:
            response = self.session.get(
                MAUDE_BASE_URL,
                params={"search": search, "count": "device.brand_name.exact", "limit": top_n},
                timeout=30,
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            return [{"product_name": item["term"], "count": item["count"]} for item in response.json().get("results", [])]
        except Exception as e:
            logger.error(f"Failed to get products for manufacturer {manufacturer}: {e}")
            return []

    # =========================================================================
    # BROAD DISCOVERY METHODS (The main discovery mode entry points)
    # =========================================================================

    def discover_device_anomalies(
        self,
        current_days: int = 30,
        baseline_days: int = 365,
        min_current_reports: int = 30,
        min_delta_pct: float = 100.0,
        include_new_entrants: bool = True,
    ) -> list[DeviceTrend]:
        """DEVICE-FIRST DISCOVERY: Find devices with anomalous adverse event increases."""
        logger.info(f"Discovering device anomalies (last {current_days} days)")
        
        now = self.reference_date
        current_devices = self.get_trending_devices(days=current_days, top_n=500)
        
        # Get baseline
        baseline_end = now - timedelta(days=baseline_days)
        baseline_start = baseline_end - timedelta(days=current_days)
        baseline_search = f"date_received:[{baseline_start.strftime('%Y-%m-%d')}+TO+{baseline_end.strftime('%Y-%m-%d')}]"
        
        try:
            response = self.session.get(
                MAUDE_BASE_URL,
                params={"search": baseline_search, "count": "device.brand_name.exact", "limit": 500},
                timeout=30,
            )
            response.raise_for_status()
            baseline_devices = {item["term"]: item["count"] for item in response.json().get("results", [])}
        except Exception:
            baseline_devices = {}

        anomalies = []
        for item in current_devices:
            device_name = item["device_name"]
            current_count = item["count"]
            
            if current_count < min_current_reports:
                continue
            
            baseline_count = baseline_devices.get(device_name, 0)
            
            if baseline_count == 0:
                if not include_new_entrants:
                    continue
                delta_pct = float("inf")
                is_new = True
            else:
                delta_pct = ((current_count - baseline_count) / baseline_count) * 100
                is_new = False
            
            if delta_pct >= min_delta_pct or is_new:
                top_problems = self._get_top_problems_for_device(device_name, now - timedelta(days=current_days), now)
                manufacturer = self._get_manufacturer_for_device(device_name, now - timedelta(days=current_days), now)
                anomalies.append(DeviceTrend(
                    source="maude",
                    device_name=device_name,
                    product_code=None,
                    manufacturer=manufacturer,
                    window_days=current_days,
                    reports_current=current_count,
                    reports_baseline=baseline_count,
                    delta_pct=delta_pct,
                    top_problems=top_problems,
                    is_new_entrant=is_new,
                ))

        anomalies.sort(key=lambda x: x.delta_pct if x.delta_pct != float("inf") else 999999, reverse=True)
        logger.info(f"Found {len(anomalies)} device anomalies")
        return anomalies

    def discover_category_anomalies(
        self,
        current_days: int = 30,
        baseline_days: int = 365,
        min_current_reports: int = 50,
        min_delta_pct: float = 50.0,
        top_n: int = 100,
    ) -> list[DeviceCategoryTrend]:
        """
        CATEGORY-FIRST DISCOVERY: Find device categories that are spiking.
        
        This catches whole classes of devices failing. Example:
        "Surgical mesh (OTN) is up 150%" → trace to specific manufacturers/brands
        """
        logger.info(f"Discovering device category anomalies (last {current_days} days)")
        
        current_codes = self.get_trending_product_codes(days=current_days, top_n=top_n)
        
        anomalies = []
        for item in current_codes:
            product_code = item["product_code"]
            current_count = item["count"]
            
            if current_count < min_current_reports:
                continue
            
            trend = self.get_category_trend(product_code, current_days, baseline_days)
            
            if trend and (trend.delta_pct >= min_delta_pct or trend.reports_baseline == 0):
                anomalies.append(trend)
                logger.debug(f"  Trending category: {product_code} ({trend.reports_current} current, {trend.delta_pct:.0f}% delta)")
        
        anomalies.sort(key=lambda x: x.delta_pct if x.delta_pct != float("inf") else 999999, reverse=True)
        logger.info(f"Found {len(anomalies)} category anomalies")
        return anomalies

    def discover_manufacturer_anomalies(
        self,
        current_days: int = 30,
        baseline_days: int = 365,
        min_current_reports: int = 50,
        min_delta_pct: float = 75.0,
        top_n: int = 100,
    ) -> list[ManufacturerTrend]:
        """
        MANUFACTURER-FIRST DISCOVERY: Find manufacturers with systemic issues.
        
        Catches companies with problems across their portfolio.
        """
        logger.info(f"Discovering manufacturer anomalies (last {current_days} days)")
        
        current_manufacturers = self.get_trending_manufacturers(days=current_days, top_n=top_n)
        
        anomalies = []
        for item in current_manufacturers:
            manufacturer = item["manufacturer"]
            current_count = item["count"]
            
            if current_count < min_current_reports:
                continue
            
            trend = self.get_manufacturer_trend(manufacturer, current_days, baseline_days)
            
            if trend and (trend.delta_pct >= min_delta_pct or trend.reports_baseline == 0):
                anomalies.append(trend)
                logger.debug(f"  Trending manufacturer: {manufacturer} ({trend.reports_current} current, {trend.delta_pct:.0f}% delta)")
        
        anomalies.sort(key=lambda x: x.delta_pct if x.delta_pct != float("inf") else 999999, reverse=True)
        logger.info(f"Found {len(anomalies)} manufacturer anomalies")
        return anomalies

    # =========================================================================
    # FULL DISCOVERY SCAN (Main entry point for Discovery Mode)
    # =========================================================================

    def run_full_discovery(self, current_days: int = 30, baseline_days: int = 365) -> dict[str, Any]:
        """
        Run all discovery methods and return consolidated results.
        This is the main entry point for Discovery Mode.
        """
        logger.info("=" * 60)
        logger.info("MAUDE FULL DISCOVERY SCAN")
        logger.info("=" * 60)
        
        results = {
            "scan_time": self.reference_date.isoformat(),
            "source": "maude",
            "parameters": {"current_days": current_days, "baseline_days": baseline_days},
            "device_anomalies": [],
            "category_anomalies": [],
            "manufacturer_anomalies": [],
            "summary": {},
        }
        
        # 1. Device-level anomalies
        try:
            device_anomalies = self.discover_device_anomalies(
                current_days=current_days, baseline_days=baseline_days,
                min_current_reports=30, min_delta_pct=100.0
            )
            results["device_anomalies"] = [
                {
                    "device_name": a.device_name,
                    "manufacturer": a.manufacturer,
                    "reports_current": a.reports_current,
                    "reports_baseline": a.reports_baseline,
                    "delta_pct": a.delta_pct if a.delta_pct != float("inf") else "new_entrant",
                    "top_problems": a.top_problems[:5],
                    "is_new_entrant": a.is_new_entrant,
                }
                for a in device_anomalies[:50]
            ]
        except Exception as e:
            logger.error(f"Device anomaly discovery failed: {e}")
        
        # 2. Category-level anomalies (key innovation for devices)
        try:
            category_anomalies = self.discover_category_anomalies(
                current_days=current_days, baseline_days=baseline_days,
                min_current_reports=50, min_delta_pct=50.0
            )
            results["category_anomalies"] = [
                {
                    "product_code": t.product_code,
                    "reports_current": t.reports_current,
                    "reports_baseline": t.reports_baseline,
                    "delta_pct": t.delta_pct if t.delta_pct != float("inf") else "new",
                    "top_manufacturers": t.top_manufacturers[:5],
                    "top_brands": t.top_brands[:5],
                }
                for t in category_anomalies[:50]
            ]
        except Exception as e:
            logger.error(f"Category anomaly discovery failed: {e}")
        
        # 3. Manufacturer-level anomalies
        try:
            manufacturer_anomalies = self.discover_manufacturer_anomalies(
                current_days=current_days, baseline_days=baseline_days,
                min_current_reports=50, min_delta_pct=75.0
            )
            results["manufacturer_anomalies"] = [
                {
                    "manufacturer": t.manufacturer,
                    "reports_current": t.reports_current,
                    "reports_baseline": t.reports_baseline,
                    "delta_pct": t.delta_pct if t.delta_pct != float("inf") else "new",
                    "top_products": t.top_products[:5],
                }
                for t in manufacturer_anomalies[:50]
            ]
        except Exception as e:
            logger.error(f"Manufacturer anomaly discovery failed: {e}")
        
        results["summary"] = {
            "device_anomalies_count": len(results["device_anomalies"]),
            "category_anomalies_count": len(results["category_anomalies"]),
            "manufacturer_anomalies_count": len(results["manufacturer_anomalies"]),
        }
        
        logger.info("=" * 60)
        logger.info(f"Discovery complete: {results['summary']}")
        logger.info("=" * 60)
        
        return results

    # Legacy alias
    def get_adverse_trend(self, device_name: str, current_days: int = 30, baseline_days: int = 365) -> DeviceTrend | None:
        return self.get_device_trend(device_name, current_days, baseline_days)
