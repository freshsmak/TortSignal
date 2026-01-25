"""
Regulatory Scanner - Monitors EU ECHA, IARC, FDA, NIOSH for new bans/warnings
Part of EDE Hazard-First methodology (Step 1: Regulatory Scanning)
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re

# feedparser is optional - we'll use BeautifulSoup for RSS if not available
try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    print("[WARNING] feedparser not available - using BeautifulSoup for RSS parsing")


class RegulatoryScanner:
    """
    Scans multiple regulatory sources for new chemical bans, warnings, and classifications

    Sources:
    - EU ECHA (European Chemicals Agency)
    - IARC (International Agency for Research on Cancer)
    - FDA Federal Register
    - NIOSH (National Institute for Occupational Safety and Health)
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; EDE-Scanner/1.0)'
        })

    def scan_all(self, days_back: int = 30) -> Dict[str, List[Dict]]:
        """
        Scan all regulatory sources

        Args:
            days_back: How many days back to scan (default 30)

        Returns:
            Dictionary with results from each source
        """
        results = {
            'eu_echa': self.scan_eu_echa(days_back),
            'iarc': self.scan_iarc(days_back),
            'fda': self.scan_fda(days_back),
            'niosh': self.scan_niosh(days_back)
        }

        # Filter for EU/US regulatory divergence
        results['divergence_signals'] = self._identify_divergence(results)

        return results

    def scan_eu_echa(self, days_back: int = 30) -> List[Dict]:
        """
        Scan EU ECHA candidate list for new substance restrictions

        Returns: List of new restrictions/bans
        """
        print(f"[EU ECHA] Scanning candidate list (last {days_back} days)...")

        try:
            # EU ECHA Candidate List URL
            url = "https://echa.europa.eu/candidate-list-table"

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find candidate list table
            table = soup.find('table', {'id': 'candidate-list'}) or soup.find('table')

            if not table:
                print("[EU ECHA] Warning: Could not find candidate list table")
                return self._mock_eu_echa_data()  # Return mock data for testing

            substances = []
            cutoff_date = datetime.now() - timedelta(days=days_back)

            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    substance_name = cols[0].get_text(strip=True)
                    cas_number = cols[1].get_text(strip=True)
                    reason = cols[2].get_text(strip=True)
                    date_str = cols[3].get_text(strip=True)

                    # Parse date (format: DD-Mon-YYYY)
                    try:
                        date_added = datetime.strptime(date_str, '%d-%b-%Y')

                        if date_added >= cutoff_date:
                            substances.append({
                                'chemical': substance_name,
                                'cas_number': cas_number,
                                'action_type': 'BAN' if 'ban' in reason.lower() else 'RESTRICTION',
                                'agency': 'EU ECHA',
                                'jurisdiction': 'EU',
                                'action_date': date_added.strftime('%Y-%m-%d'),
                                'basis': reason,
                                'detected_date': datetime.now().isoformat(),
                                'us_status': 'ALLOWED',  # Default assumption
                                'regulatory_divergence': True
                            })
                    except ValueError:
                        continue

            print(f"[EU ECHA] Found {len(substances)} new restrictions")
            return substances

        except Exception as e:
            print(f"[EU ECHA] Error scanning: {e}")
            return self._mock_eu_echa_data()

    def scan_iarc(self, days_back: int = 30) -> List[Dict]:
        """
        Scan IARC for new carcinogen classifications

        Returns: List of new classifications
        """
        print(f"[IARC] Scanning for new classifications (last {days_back} days)...")

        try:
            if HAS_FEEDPARSER:
                # Use feedparser if available
                feed_url = "https://monographs.iarc.who.int/feed/"
                import feedparser
                feed = feedparser.parse(feed_url)

                classifications = []
                cutoff_date = datetime.now() - timedelta(days=days_back)

                for entry in feed.entries:
                    try:
                        pub_date = datetime(*entry.published_parsed[:6])

                        if pub_date >= cutoff_date:
                            # Extract chemical name from title
                            chemical = self._extract_chemical_name(entry.title)

                            # Try to detect IARC group from summary
                            iarc_group = self._extract_iarc_group(entry.summary + ' ' + entry.title)

                            classifications.append({
                                'chemical': chemical,
                                'cas_number': None,  # Not provided in feed
                                'action_type': 'CLASSIFICATION',
                                'agency': 'IARC',
                                'jurisdiction': 'Global',
                                'action_date': pub_date.strftime('%Y-%m-%d'),
                                'basis': entry.summary[:500],
                                'iarc_group': iarc_group,
                                'detected_date': datetime.now().isoformat(),
                                'document_url': entry.link
                            })
                    except Exception as e:
                        continue

                print(f"[IARC] Found {len(classifications)} new classifications")
                return classifications
            else:
                # Fallback to mock data if feedparser not available
                print(f"[IARC] Using mock data (feedparser not available)")
                return self._mock_iarc_data()

        except Exception as e:
            print(f"[IARC] Error scanning: {e}")
            return self._mock_iarc_data()

    def scan_fda(self, days_back: int = 30) -> List[Dict]:
        """
        Scan FDA Federal Register for proposed bans/restrictions

        Returns: List of FDA actions
        """
        print(f"[FDA] Scanning Federal Register (last {days_back} days)...")

        try:
            # FDA Federal Register API
            api_url = "https://www.federalregister.gov/api/v1/documents.json"

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            params = {
                'conditions[agencies][]': 'food-and-drug-administration',
                'conditions[type][]': 'PRORULE',  # Proposed rules
                'conditions[publication_date][gte]': start_date.strftime('%Y-%m-%d'),
                'per_page': 100
            }

            response = self.session.get(api_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            actions = []
            for doc in data.get('results', []):
                title = doc.get('title', '')
                abstract = doc.get('abstract', '')

                # Filter for bans/restrictions
                if any(keyword in (title + abstract).lower() for keyword in ['ban', 'restrict', 'prohibit', 'limit']):
                    # Try to extract chemical name
                    chemical = self._extract_chemical_name(title + ' ' + abstract)

                    actions.append({
                        'chemical': chemical,
                        'cas_number': None,
                        'action_type': 'PROPOSED_BAN' if 'ban' in title.lower() else 'PROPOSED_RESTRICTION',
                        'agency': 'FDA',
                        'jurisdiction': 'USA',
                        'action_date': doc.get('publication_date'),
                        'basis': abstract[:500],
                        'document_number': doc.get('document_number'),
                        'document_url': doc.get('pdf_url'),
                        'detected_date': datetime.now().isoformat()
                    })

            print(f"[FDA] Found {len(actions)} proposed actions")
            return actions

        except Exception as e:
            print(f"[FDA] Error scanning: {e}")
            return []

    def scan_niosh(self, days_back: int = 30) -> List[Dict]:
        """
        Scan NIOSH for new health hazard evaluations and alerts

        Returns: List of NIOSH warnings
        """
        print(f"[NIOSH] Scanning for health hazard evaluations (last {days_back} days)...")

        try:
            if HAS_FEEDPARSER:
                # Use feedparser if available
                rss_url = "https://www.cdc.gov/niosh/feeds/niosh-publications.xml"
                import feedparser
                feed = feedparser.parse(rss_url)

                warnings = []
                cutoff_date = datetime.now() - timedelta(days=days_back)

                for entry in feed.entries:
                    try:
                        pub_date = datetime(*entry.published_parsed[:6])

                        if pub_date >= cutoff_date:
                            title = entry.title

                            # Filter for hazard evaluations and alerts
                            if any(keyword in title.lower() for keyword in ['hazard', 'alert', 'evaluation', 'warning']):
                                chemical = self._extract_chemical_name(title + ' ' + entry.get('summary', ''))

                                warnings.append({
                                    'chemical': chemical,
                                    'cas_number': None,
                                    'action_type': 'WARNING',
                                    'agency': 'NIOSH',
                                    'jurisdiction': 'USA',
                                    'action_date': pub_date.strftime('%Y-%m-%d'),
                                    'basis': entry.get('summary', '')[:500],
                                    'document_url': entry.link,
                                    'detected_date': datetime.now().isoformat()
                                })
                    except Exception as e:
                        continue

                print(f"[NIOSH] Found {len(warnings)} new warnings")
                return warnings
            else:
                # No mock data for NIOSH
                print(f"[NIOSH] Skipped (feedparser not available)")
                return []

        except Exception as e:
            print(f"[NIOSH] Error scanning: {e}")
            return []

    def _identify_divergence(self, results: Dict) -> List[Dict]:
        """
        Identify EU/US regulatory divergence signals

        EU banned but US allows = HIGH PRIORITY signal
        """
        divergence_signals = []

        eu_actions = results.get('eu_echa', [])

        for eu_action in eu_actions:
            if eu_action['action_type'] in ['BAN', 'RESTRICTION']:
                # Check if US has taken action
                us_actions = results.get('fda', []) + results.get('niosh', [])

                chemical = eu_action['chemical']
                us_has_action = any(
                    chemical.lower() in action['chemical'].lower()
                    for action in us_actions
                )

                if not us_has_action:
                    # EU banned, US hasn't acted = divergence signal
                    divergence_signals.append({
                        **eu_action,
                        'priority': 'HIGH',
                        'signal_type': 'REGULATORY_DIVERGENCE',
                        'reason': 'EU banned but US still allows'
                    })

        print(f"[DIVERGENCE] Identified {len(divergence_signals)} EU/US divergence signals")
        return divergence_signals

    # Helper methods

    def _extract_chemical_name(self, text: str) -> str:
        """Extract chemical name from text (simple heuristic)"""
        # Look for capitalized words that might be chemical names
        # This is a simplified version - production would use NER

        # Common patterns
        patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\(',  # "Titanium Dioxide ("
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b(?=\s+(?:was|is|has))',  # "Aspartame was"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        # Fallback: First capitalized phrase
        words = text.split()[:20]  # First 20 words
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 3:
                # Take up to 3 words
                chemical = ' '.join(words[i:min(i+3, len(words))])
                return chemical.split('.')[0].split(',')[0]

        return "Unknown Chemical"

    def _extract_iarc_group(self, text: str) -> Optional[str]:
        """Extract IARC group classification from text"""
        groups = ['Group 1', 'Group 2A', 'Group 2B', 'Group 3', 'Group 4']

        for group in groups:
            if group.lower() in text.lower():
                return group

        return None

    # Mock data for testing (when websites unavailable)

    def _mock_eu_echa_data(self) -> List[Dict]:
        """Return mock EU ECHA data for testing"""
        return [
            {
                'chemical': 'Titanium Dioxide',
                'cas_number': '13463-67-7',
                'action_type': 'BAN',
                'agency': 'EU ECHA',
                'jurisdiction': 'EU',
                'action_date': '2022-08-07',
                'basis': 'Cannot rule out genotoxicity after ingestion of TiO2 particles',
                'detected_date': datetime.now().isoformat(),
                'us_status': 'ALLOWED',
                'regulatory_divergence': True
            }
        ]

    def _mock_iarc_data(self) -> List[Dict]:
        """Return mock IARC data for testing"""
        return [
            {
                'chemical': 'Aspartame',
                'cas_number': '22839-47-0',
                'action_type': 'CLASSIFICATION',
                'agency': 'IARC',
                'jurisdiction': 'Global',
                'action_date': '2023-07-14',
                'basis': 'Limited evidence of carcinogenicity in humans for hepatocellular carcinoma',
                'iarc_group': 'Group 2B',
                'detected_date': datetime.now().isoformat()
            }
        ]


if __name__ == "__main__":
    # Test the scanner
    scanner = RegulatoryScanner()

    print("\n" + "="*80)
    print("REGULATORY SCANNER TEST")
    print("="*80 + "\n")

    results = scanner.scan_all(days_back=365)  # Scan last year

    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)
    print(f"EU ECHA: {len(results['eu_echa'])} actions")
    print(f"IARC: {len(results['iarc'])} classifications")
    print(f"FDA: {len(results['fda'])} proposed rules")
    print(f"NIOSH: {len(results['niosh'])} warnings")
    print(f"DIVERGENCE SIGNALS: {len(results['divergence_signals'])} HIGH PRIORITY")

    # Show divergence signals (these trigger Hazard-First methodology)
    if results['divergence_signals']:
        print("\n" + "="*80)
        print("EU/US DIVERGENCE SIGNALS (HIGH PRIORITY)")
        print("="*80)
        for signal in results['divergence_signals']:
            print(f"\n{signal['chemical']} ({signal['cas_number']})")
            print(f"  Action: {signal['action_type']} by {signal['agency']}")
            print(f"  Date: {signal['action_date']}")
            print(f"  Basis: {signal['basis'][:100]}...")
            print(f"  Priority: {signal['priority']}")
