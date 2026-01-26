"""
Data Persistence Layer - Saves scan results to PostgreSQL database
Provides high-level functions to store regulatory actions, PubMed papers, and epidemiology data
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import List, Dict, Optional
import os

# Import models
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import (
    Signal, RegulatoryAction, PubMedPaper, BradfordHillScore,
    LitigationScore, EpidemiologyValidation, Exposure, Base
)


class DataPersistence:
    """
    Handles all database persistence operations for EDE
    """

    def __init__(self, database_url: str = None):
        """
        Initialize database connection

        Args:
            database_url: PostgreSQL connection string
                         Default: postgresql://postgres@localhost/ede
        """
        if database_url is None:
            # Try peer authentication first (works for local postgres user)
            database_url = os.getenv(
                'DATABASE_URL',
                'postgresql:///ede'  # Uses peer authentication
            )

        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()

    # ============================================================================
    # SIGNAL OPERATIONS
    # ============================================================================

    def create_or_update_signal(
        self,
        signal_id: str,
        chemical: str,
        disease: str,
        methodology: str = 'HAZARD_FIRST',
        status: str = 'DETECTED',
        bradford_hill_score: Optional[float] = None,
        litigation_score: Optional[float] = None
    ) -> Signal:
        """
        Create or update a signal

        Returns:
            Signal object
        """
        session = self.get_session()

        try:
            # Check if signal exists
            signal = session.query(Signal).filter_by(signal_id=signal_id).first()

            if signal:
                # Update existing
                signal.chemical = chemical
                signal.disease = disease
                signal.methodology = methodology
                signal.status = status
                signal.bradford_hill_score = bradford_hill_score
                signal.litigation_score = litigation_score
                signal.date_updated = datetime.now()
            else:
                # Create new
                signal = Signal(
                    signal_id=signal_id,
                    chemical=chemical,
                    disease=disease,
                    methodology=methodology,
                    status=status,
                    bradford_hill_score=bradford_hill_score,
                    litigation_score=litigation_score,
                    date_detected=datetime.now(),
                    date_updated=datetime.now()
                )
                session.add(signal)

            session.commit()
            session.refresh(signal)

            print(f"[DB] Signal {signal_id} saved: {chemical} → {disease} ({status})")

            return signal

        except Exception as e:
            session.rollback()
            print(f"[DB] Error saving signal: {e}")
            raise
        finally:
            session.close()

    def get_signal(self, signal_id: str) -> Optional[Signal]:
        """Get a signal by ID"""
        session = self.get_session()
        try:
            return session.query(Signal).filter_by(signal_id=signal_id).first()
        finally:
            session.close()

    # ============================================================================
    # REGULATORY ACTIONS
    # ============================================================================

    def save_regulatory_actions(
        self,
        signal_id: str,
        actions: List[Dict]
    ) -> int:
        """
        Save regulatory actions to database

        Args:
            signal_id: Signal ID
            actions: List of regulatory action dicts from scanner

        Returns:
            Number of actions saved
        """
        session = self.get_session()

        try:
            # Get signal
            signal = session.query(Signal).filter_by(signal_id=signal_id).first()
            if not signal:
                raise ValueError(f"Signal {signal_id} not found")

            saved_count = 0

            for action in actions:
                # Check if action already exists
                existing = session.query(RegulatoryAction).filter_by(
                    signal_id=signal.id,
                    agency=action.get('agency'),
                    action_date=action.get('action_date')
                ).first()

                if not existing:
                    reg_action = RegulatoryAction(
                        signal_id=signal.id,
                        action_type=action.get('action_type'),
                        agency=action.get('agency'),
                        jurisdiction=action.get('jurisdiction'),
                        action_date=action.get('action_date'),
                        basis=action.get('basis'),
                        document_url=action.get('document_url'),
                        regulatory_divergence=action.get('regulatory_divergence', False),
                        detected_date=datetime.now()
                    )
                    session.add(reg_action)
                    saved_count += 1

            session.commit()
            print(f"[DB] Saved {saved_count} regulatory actions for {signal_id}")

            return saved_count

        except Exception as e:
            session.rollback()
            print(f"[DB] Error saving regulatory actions: {e}")
            raise
        finally:
            session.close()

    # ============================================================================
    # PUBMED PAPERS
    # ============================================================================

    def save_pubmed_papers(
        self,
        signal_id: str,
        papers: List[Dict]
    ) -> int:
        """
        Save PubMed papers to database

        Args:
            signal_id: Signal ID
            papers: List of paper dicts from PubMed integration

        Returns:
            Number of papers saved
        """
        session = self.get_session()

        try:
            # Get signal
            signal = session.query(Signal).filter_by(signal_id=signal_id).first()
            if not signal:
                raise ValueError(f"Signal {signal_id} not found")

            saved_count = 0

            for paper in papers:
                # Check if paper already exists
                existing = session.query(PubMedPaper).filter_by(
                    pmid=paper.get('pmid')
                ).first()

                if not existing:
                    # Convert year to date if available
                    pub_date = None
                    if paper.get('year'):
                        try:
                            pub_date = datetime(int(paper.get('year')), 1, 1).date()
                        except:
                            pass

                    pubmed_paper = PubMedPaper(
                        signal_id=signal.id,
                        pmid=paper.get('pmid'),
                        title=paper.get('title'),
                        abstract=paper.get('abstract'),
                        authors=', '.join(paper.get('authors', [])),
                        journal=paper.get('journal'),
                        publication_date=pub_date,
                        paper_type=paper.get('evidence_type'),  # Map evidence_type to paper_type
                        created_at=datetime.now()
                    )
                    session.add(pubmed_paper)
                    saved_count += 1

            session.commit()
            print(f"[DB] Saved {saved_count} PubMed papers for {signal_id}")

            return saved_count

        except Exception as e:
            session.rollback()
            print(f"[DB] Error saving PubMed papers: {e}")
            raise
        finally:
            session.close()

    # ============================================================================
    # EPIDEMIOLOGY VALIDATION
    # ============================================================================

    def save_epidemiology_validation(
        self,
        signal_id: str,
        data_source: str,  # 'CDC_WONDER' or 'SEER'
        disease: str,
        disease_trend: Dict,
        temporality_assessment: Dict
    ) -> EpidemiologyValidation:
        """
        Save epidemiology validation results

        Args:
            signal_id: Signal ID
            data_source: CDC_WONDER or SEER
            disease: Disease name
            disease_trend: Disease trend data from epidemiology integration
            temporality_assessment: Temporality validation results

        Returns:
            EpidemiologyValidation object
        """
        session = self.get_session()

        try:
            # Get signal
            signal = session.query(Signal).filter_by(signal_id=signal_id).first()
            if not signal:
                raise ValueError(f"Signal {signal_id} not found")

            # Get years
            years = disease_trend.get('years', [])
            timeframe = f"{years[0]}-{years[-1]}" if years else None

            # Get exposure/disease periods from temporality assessment
            exposure_start = temporality_assessment.get('exposure_start_year')
            disease_increase = temporality_assessment.get('disease_increase_year')
            exposure_period = f"{exposure_start}-present" if exposure_start else None
            disease_period = f"{disease_increase}-present" if disease_increase else None

            # Determine validation result
            score = temporality_assessment.get('bradford_hill_score', 0)
            if score >= 8:
                validation_result = 'STRONG'
            elif score >= 6:
                validation_result = 'MODERATE'
            elif score >= 3:
                validation_result = 'WEAK'
            else:
                validation_result = 'NONE'

            # Check if validation exists
            existing = session.query(EpidemiologyValidation).filter_by(
                signal_id=signal.id,
                data_source=data_source
            ).first()

            if existing:
                # Update
                existing.disease = disease
                existing.baseline_rate = disease_trend.get('rates', [None])[0]
                existing.current_rate = disease_trend.get('rates', [None])[-1]
                existing.percent_change = disease_trend.get('percent_change')
                existing.timeframe = timeframe
                existing.exposure_period = exposure_period
                existing.disease_period = disease_period
                existing.latency_years = temporality_assessment.get('latency_period')
                existing.temporal_correlation_score = temporality_assessment.get('bradford_hill_score')
                existing.validation_result = validation_result
                existing.created_at = datetime.now()

                epi_validation = existing
            else:
                # Create new
                epi_validation = EpidemiologyValidation(
                    signal_id=signal.id,
                    data_source=data_source,
                    disease=disease,
                    baseline_rate=disease_trend.get('rates', [None])[0],
                    current_rate=disease_trend.get('rates', [None])[-1],
                    percent_change=disease_trend.get('percent_change'),
                    timeframe=timeframe,
                    exposure_period=exposure_period,
                    disease_period=disease_period,
                    latency_years=temporality_assessment.get('latency_period'),
                    temporal_correlation_score=temporality_assessment.get('bradford_hill_score'),
                    validation_result=validation_result,
                    created_at=datetime.now()
                )
                session.add(epi_validation)

            session.commit()
            session.refresh(epi_validation)

            print(f"[DB] Saved epidemiology validation for {signal_id}: {validation_result} (temporality: {temporality_assessment.get('bradford_hill_score')}/10)")

            return epi_validation

        except Exception as e:
            session.rollback()
            print(f"[DB] Error saving epidemiology validation: {e}")
            raise
        finally:
            session.close()

    # ============================================================================
    # BRADFORD HILL SCORES
    # ============================================================================

    def save_bradford_hill_score(
        self,
        signal_id: str,
        result
    ) -> BradfordHillScore:
        """
        Save Bradford Hill score to database

        Args:
            signal_id: Signal ID
            result: BradfordHillResult from scorer

        Returns:
            BradfordHillScore object
        """
        session = self.get_session()

        try:
            # Get signal
            signal = session.query(Signal).filter_by(signal_id=signal_id).first()
            if not signal:
                raise ValueError(f"Signal {signal_id} not found")

            # Extract criterion scores
            cs = result.criteria_scores

            # Check if score exists
            existing = session.query(BradfordHillScore).filter_by(
                signal_id=signal.id
            ).first()

            if existing:
                # Update
                existing.strength_score = cs['strength']['score']
                existing.consistency_score = cs['consistency']['score']
                existing.specificity_score = cs['specificity']['score']
                existing.temporality_score = cs['temporality']['score']
                existing.biological_gradient_score = cs['biological_gradient']['score']
                existing.plausibility_score = cs['plausibility']['score']
                existing.coherence_score = cs['coherence']['score']
                existing.experiment_score = cs['experiment']['score']
                existing.analogy_score = cs['analogy']['score']
                existing.composite_score = float(result.composite_score)
                existing.interpretation = result.interpretation
                existing.evidence = dict(result.criteria_scores)
                existing.scored_date = datetime.now()

                bh_score = existing
            else:
                # Create new
                bh_score = BradfordHillScore(
                    signal_id=signal.id,
                    strength_score=cs['strength']['score'],
                    consistency_score=cs['consistency']['score'],
                    specificity_score=cs['specificity']['score'],
                    temporality_score=cs['temporality']['score'],
                    biological_gradient_score=cs['biological_gradient']['score'],
                    plausibility_score=cs['plausibility']['score'],
                    coherence_score=cs['coherence']['score'],
                    experiment_score=cs['experiment']['score'],
                    analogy_score=cs['analogy']['score'],
                    composite_score=float(result.composite_score),
                    interpretation=result.interpretation,
                    evidence=dict(result.criteria_scores),
                    scored_date=datetime.now()
                )
                session.add(bh_score)

            # Update signal score
            signal.bradford_hill_score = float(result.composite_score)
            signal.date_updated = datetime.now()

            session.commit()
            session.refresh(bh_score)

            print(f"[DB] Saved Bradford Hill score for {signal_id}: {result.composite_score}/100")

            return bh_score

        except Exception as e:
            session.rollback()
            print(f"[DB] Error saving Bradford Hill score: {e}")
            raise
        finally:
            session.close()

    # ============================================================================
    # QUERY OPERATIONS
    # ============================================================================

    def get_all_signals(self, status: Optional[str] = None) -> List[Signal]:
        """Get all signals, optionally filtered by status"""
        session = self.get_session()
        try:
            query = session.query(Signal)
            if status:
                query = query.filter_by(status=status)
            return query.order_by(Signal.litigation_score.desc()).all()
        finally:
            session.close()

    def get_signals_for_validation(self) -> List[Signal]:
        """Get signals that are ready for validation (BH >= 85)"""
        session = self.get_session()
        try:
            return session.query(Signal).filter(
                Signal.bradford_hill_score >= 85,
                Signal.status == 'READY_TO_VALIDATE'
            ).order_by(Signal.litigation_score.desc()).all()
        finally:
            session.close()


if __name__ == "__main__":
    # Test the persistence layer
    print("\n" + "="*80)
    print("DATA PERSISTENCE LAYER TEST")
    print("="*80 + "\n")

    db = DataPersistence()

    # Test 1: Create a test signal
    print("Test 1: Creating test signal...")
    signal = db.create_or_update_signal(
        signal_id="TEST-2026-001",
        chemical="Test Chemical",
        disease="Test Disease",
        methodology="HAZARD_FIRST",
        status="DETECTED"
    )
    print(f"✓ Signal created: {signal.signal_id}")

    # Test 2: Save regulatory action
    print("\nTest 2: Saving regulatory action...")
    actions = [{
        'chemical': 'Test Chemical',
        'action_type': 'BAN',
        'agency': 'EU ECHA',
        'jurisdiction': 'EU',
        'action_date': '2024-01-01',
        'basis': 'Test basis',
        'regulatory_divergence': True
    }]
    count = db.save_regulatory_actions("TEST-2026-001", actions)
    print(f"✓ Saved {count} regulatory actions")

    # Test 3: Save PubMed papers
    print("\nTest 3: Saving PubMed papers...")
    papers = [{
        'pmid': '12345678',
        'title': 'Test Paper Title',
        'abstract': 'Test abstract',
        'authors': ['Smith J', 'Jones A'],
        'journal': 'Test Journal',
        'year': '2023',
        'evidence_type': 'MECHANISTIC',
        'extracted_evidence': {'pathways': ['inflammation']}
    }]
    count = db.save_pubmed_papers("TEST-2026-001", papers)
    print(f"✓ Saved {count} PubMed papers")

    # Test 4: Get all signals
    print("\nTest 4: Querying signals...")
    signals = db.get_all_signals()
    print(f"✓ Found {len(signals)} total signals")
    for sig in signals:
        print(f"  - {sig.signal_id}: {sig.chemical} → {sig.disease} ({sig.status})")

    print("\n✅ DATA PERSISTENCE LAYER TEST COMPLETE")
