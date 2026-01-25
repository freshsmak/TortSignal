"""
SQLAlchemy models for EDE database
Maps to PostgreSQL schema defined in database/schema.sql
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, BigInteger, Boolean, DateTime,
    Text, Date, ForeignKey, CheckConstraint, Index, DECIMAL
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class Signal(Base):
    """Core table storing all detected regulatory/epidemiological signals"""
    __tablename__ = 'signals'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id = Column(String(50), unique=True, nullable=False)

    # Core identifiers
    chemical = Column(String(255), nullable=False)
    cas_number = Column(String(50))
    disease = Column(String(255), nullable=False)
    disease_code = Column(String(50))

    # Methodology
    methodology = Column(String(50), nullable=False)  # HAZARD_FIRST, EPIDEMIOLOGY_FIRST

    # Status tracking
    status = Column(String(50), nullable=False, default='DETECTED')

    # Dates
    date_detected = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_updated = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Scores (cached)
    bradford_hill_score = Column(DECIMAL(5, 2))
    litigation_score = Column(DECIMAL(5, 2))

    # Market sizing (cached)
    market_size_min = Column(BigInteger)
    market_size_max = Column(BigInteger)
    addressable_plaintiffs_min = Column(Integer)
    addressable_plaintiffs_max = Column(Integer)

    # Archive reason
    archive_reason = Column(Text)

    # Metadata
    created_by = Column(String(100), default='EDE_AUTOMATED')
    notes = Column(Text)

    # Relationships
    regulatory_actions = relationship("RegulatoryAction", back_populates="signal", cascade="all, delete-orphan")
    exposures = relationship("Exposure", back_populates="signal", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="signal", cascade="all, delete-orphan")
    epidemiology_validations = relationship("EpidemiologyValidation", back_populates="signal", cascade="all, delete-orphan")
    bradford_hill_scores = relationship("BradfordHillScore", back_populates="signal", cascade="all, delete-orphan")
    litigation_scores = relationship("LitigationScore", back_populates="signal", cascade="all, delete-orphan")
    defendants = relationship("Defendant", back_populates="signal", cascade="all, delete-orphan")
    pubmed_papers = relationship("PubMedPaper", back_populates="signal", cascade="all, delete-orphan")
    litigation_status = relationship("LitigationStatus", back_populates="signal", cascade="all, delete-orphan")
    user_actions = relationship("UserAction", back_populates="signal", cascade="all, delete-orphan")
    dossiers = relationship("DiscoveryDossier", back_populates="signal", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "(bradford_hill_score IS NULL OR bradford_hill_score BETWEEN 0 AND 100) AND "
            "(litigation_score IS NULL OR litigation_score BETWEEN 0 AND 150)",
            name='check_scores'
        ),
        Index('idx_signals_status', 'status'),
        Index('idx_signals_scores', 'bradford_hill_score', 'litigation_score'),
        Index('idx_signals_date_detected', 'date_detected'),
        Index('idx_signals_methodology', 'methodology'),
    )

    def __repr__(self):
        return f"<Signal {self.signal_id}: {self.chemical} → {self.disease} (BH: {self.bradford_hill_score}, Lit: {self.litigation_score})>"


class RegulatoryAction(Base):
    """Tracks all regulatory signals (EU bans, IARC classifications, FDA actions)"""
    __tablename__ = 'regulatory_actions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey('signals.id', ondelete='CASCADE'), nullable=False)

    # Action details
    action_type = Column(String(50), nullable=False)  # BAN, RESTRICTION, WARNING, CLASSIFICATION
    agency = Column(String(100), nullable=False)
    jurisdiction = Column(String(100), nullable=False)

    # Dates
    action_date = Column(Date, nullable=False)
    effective_date = Column(Date)
    detected_date = Column(DateTime, default=datetime.utcnow)

    # Details
    basis = Column(Text)
    document_url = Column(Text)
    document_number = Column(String(100))

    # IARC specific
    iarc_group = Column(String(10))

    # US status comparison
    us_status = Column(String(50))
    regulatory_divergence = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    signal = relationship("Signal", back_populates="regulatory_actions")

    __table_args__ = (
        Index('idx_regulatory_signal', 'signal_id'),
        Index('idx_regulatory_date', 'action_date'),
        Index('idx_regulatory_divergence', 'regulatory_divergence'),
    )


class Exposure(Base):
    """Maps chemicals to products and exposed populations"""
    __tablename__ = 'exposures'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey('signals.id', ondelete='CASCADE'), nullable=False)

    # Product details
    product_name = Column(String(255))
    manufacturer = Column(String(255))
    product_category = Column(String(100))

    # Exposure details
    chemical_concentration = Column(String(100))
    exposure_route = Column(String(50))

    # Population
    exposed_population_estimate = Column(BigInteger)
    demographics = Column(JSONB)

    # Intensity
    frequency = Column(String(100))
    duration = Column(String(100))
    exposure_intensity_score = Column(DECIMAL(3, 1))

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    signal = relationship("Signal", back_populates="exposures")

    __table_args__ = (
        Index('idx_exposures_signal', 'signal_id'),
    )


class Prediction(Base):
    """Stores predicted outcomes based on mechanisms"""
    __tablename__ = 'predictions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey('signals.id', ondelete='CASCADE'), nullable=False)

    # Predicted disease
    predicted_disease = Column(String(255), nullable=False)
    predicted_disease_code = Column(String(50))
    confidence_score = Column(DECIMAL(3, 2))

    # Mechanisms
    mechanisms = Column(JSONB)

    # Evidence counts
    mechanistic_papers_count = Column(Integer)
    case_reports_count = Column(Integer)
    animal_studies_count = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    signal = relationship("Signal", back_populates="predictions")

    __table_args__ = (
        Index('idx_predictions_signal', 'signal_id'),
    )


class EpidemiologyValidation(Base):
    """Stores epidemiological validation data (SEER, CDC WONDER)"""
    __tablename__ = 'epidemiology_validations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey('signals.id', ondelete='CASCADE'), nullable=False)

    # Data source
    data_source = Column(String(50), nullable=False)

    # Trends
    disease = Column(String(255), nullable=False)
    demographics = Column(JSONB)

    baseline_rate = Column(DECIMAL(10, 2))
    current_rate = Column(DECIMAL(10, 2))
    percent_change = Column(DECIMAL(5, 2))

    timeframe = Column(String(50))

    # Temporal correlation
    exposure_period = Column(String(50))
    disease_period = Column(String(50))
    latency_years = Column(Integer)
    temporal_correlation_score = Column(DECIMAL(3, 1))

    validation_result = Column(String(50))  # STRONG, MODERATE, WEAK, NONE

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    signal = relationship("Signal", back_populates="epidemiology_validations")

    __table_args__ = (
        Index('idx_epidemiology_signal', 'signal_id'),
    )


class BradfordHillScore(Base):
    """Detailed breakdown of 9 Bradford Hill criteria"""
    __tablename__ = 'bradford_hill_scores'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey('signals.id', ondelete='CASCADE'), nullable=False)

    # Individual criterion scores (0-10)
    strength_score = Column(DECIMAL(3, 1))
    consistency_score = Column(DECIMAL(3, 1))
    specificity_score = Column(DECIMAL(3, 1))
    temporality_score = Column(DECIMAL(3, 1))
    biological_gradient_score = Column(DECIMAL(3, 1))
    plausibility_score = Column(DECIMAL(3, 1))
    coherence_score = Column(DECIMAL(3, 1))
    experiment_score = Column(DECIMAL(3, 1))
    analogy_score = Column(DECIMAL(3, 1))

    # Weighted scores
    strength_weighted = Column(DECIMAL(5, 2))
    consistency_weighted = Column(DECIMAL(5, 2))
    specificity_weighted = Column(DECIMAL(5, 2))
    temporality_weighted = Column(DECIMAL(5, 2))
    biological_gradient_weighted = Column(DECIMAL(5, 2))
    plausibility_weighted = Column(DECIMAL(5, 2))
    coherence_weighted = Column(DECIMAL(5, 2))
    experiment_weighted = Column(DECIMAL(5, 2))
    analogy_weighted = Column(DECIMAL(5, 2))

    # Composite
    composite_score = Column(DECIMAL(5, 2), nullable=False)
    interpretation = Column(String(50))

    # Evidence (JSONB for flexibility)
    evidence = Column(JSONB)

    scored_at = Column(DateTime, default=datetime.utcnow)
    scored_by = Column(String(100), default='EDE_AUTOMATED')

    # Relationships
    signal = relationship("Signal", back_populates="bradford_hill_scores")

    __table_args__ = (
        Index('idx_bradford_hill_signal', 'signal_id'),
        Index('idx_bradford_hill_composite', 'composite_score'),
    )


class LitigationScore(Base):
    """Detailed breakdown of 7 litigation viability factors"""
    __tablename__ = 'litigation_scores'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey('signals.id', ondelete='CASCADE'), nullable=False)

    # Individual factor scores (0-10)
    causal_strength_score = Column(DECIMAL(3, 1))
    population_size_score = Column(DECIMAL(3, 1))
    defendant_solvency_score = Column(DECIMAL(3, 1))
    preventability_score = Column(DECIMAL(3, 1))
    social_justice_score = Column(DECIMAL(3, 1))
    severity_score = Column(DECIMAL(3, 1))
    novelty_score = Column(DECIMAL(3, 1))

    # Weighted scores
    causal_strength_weighted = Column(DECIMAL(5, 2))
    population_size_weighted = Column(DECIMAL(5, 2))
    defendant_solvency_weighted = Column(DECIMAL(5, 2))
    preventability_weighted = Column(DECIMAL(5, 2))
    social_justice_weighted = Column(DECIMAL(5, 2))
    severity_weighted = Column(DECIMAL(5, 2))
    novelty_weighted = Column(DECIMAL(5, 2))

    # Composite
    composite_score = Column(DECIMAL(5, 2), nullable=False)
    interpretation = Column(String(50))

    # Evidence
    evidence = Column(JSONB)

    scored_at = Column(DateTime, default=datetime.utcnow)
    scored_by = Column(String(100), default='EDE_AUTOMATED')

    # Relationships
    signal = relationship("Signal", back_populates="litigation_scores")

    __table_args__ = (
        Index('idx_litigation_signal', 'signal_id'),
        Index('idx_litigation_composite', 'composite_score'),
    )


class Defendant(Base):
    """Tracks potential defendant companies"""
    __tablename__ = 'defendants'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey('signals.id', ondelete='CASCADE'), nullable=False)

    company_name = Column(String(255), nullable=False)
    ticker_symbol = Column(String(10))

    # Financials
    annual_revenue = Column(BigInteger)
    market_cap = Column(BigInteger)
    is_public = Column(Boolean)

    # Product relationship
    product_manufacturer = Column(Boolean, default=False)
    chemical_manufacturer = Column(Boolean, default=False)

    # Insurance
    has_product_liability_insurance = Column(Boolean)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    signal = relationship("Signal", back_populates="defendants")

    __table_args__ = (
        Index('idx_defendants_signal', 'signal_id'),
    )


class PubMedPaper(Base):
    """Stores relevant PubMed papers for each signal"""
    __tablename__ = 'pubmed_papers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey('signals.id', ondelete='CASCADE'), nullable=False)

    pmid = Column(String(20), nullable=False)
    title = Column(Text, nullable=False)
    abstract = Column(Text)
    authors = Column(Text)
    journal = Column(String(255))
    publication_date = Column(Date)

    # Classification
    paper_type = Column(String(50))  # MECHANISTIC, EPIDEMIOLOGY, CASE_REPORT, REVIEW, META_ANALYSIS

    # Relevance
    relevance_score = Column(DECIMAL(3, 2))

    # Citations
    citation_count = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    signal = relationship("Signal", back_populates="pubmed_papers")

    __table_args__ = (
        Index('idx_pubmed_signal', 'signal_id'),
        Index('idx_pubmed_type', 'paper_type'),
    )


class LitigationStatus(Base):
    """Tracks pre-litigation confirmation (PACER searches, etc.)"""
    __tablename__ = 'litigation_status'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey('signals.id', ondelete='CASCADE'), nullable=False)

    # PACER search results
    pacer_cases_count = Column(Integer, default=0)
    pacer_last_searched = Column(DateTime)

    # MDL status
    mdl_status = Column(String(50))  # NONE, PETITION, FORMED
    mdl_number = Column(String(20))

    # Media coverage
    media_coverage_count = Column(Integer, default=0)
    media_last_searched = Column(DateTime)

    # Academic publications
    recent_publications_count = Column(Integer, default=0)

    # Overall novelty assessment
    is_pre_litigation = Column(Boolean, default=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    signal = relationship("Signal", back_populates="litigation_status")

    __table_args__ = (
        Index('idx_litigation_signal', 'signal_id'),
        Index('idx_litigation_pre', 'is_pre_litigation'),
    )


class UserAction(Base):
    """Tracks user interactions with signals"""
    __tablename__ = 'user_actions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey('signals.id', ondelete='CASCADE'), nullable=False)

    action_type = Column(String(50), nullable=False)
    action_data = Column(JSONB)

    performed_by = Column(String(100), default='chase@auditlab.com')
    performed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    signal = relationship("Signal", back_populates="user_actions")

    __table_args__ = (
        Index('idx_user_actions_signal', 'signal_id'),
        Index('idx_user_actions_type', 'action_type'),
        Index('idx_user_actions_date', 'performed_at'),
    )


class DiscoveryDossier(Base):
    """Tracks generated PDF dossiers"""
    __tablename__ = 'discovery_dossiers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey('signals.id', ondelete='CASCADE'), nullable=False)

    file_path = Column(Text, nullable=False)
    file_size_bytes = Column(BigInteger)

    generated_at = Column(DateTime, default=datetime.utcnow)
    generated_by = Column(String(100), default='EDE_AUTOMATED')

    version = Column(Integer, default=1)

    # Relationships
    signal = relationship("Signal", back_populates="dossiers")

    __table_args__ = (
        Index('idx_dossiers_signal', 'signal_id'),
    )
