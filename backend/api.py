"""
FastAPI application for EDE backend
Exposes REST API endpoints for signal management, scoring, and discovery generation
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, desc, and_
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
from pydantic import BaseModel
from decimal import Decimal
import os

from models import (
    Base, Signal, RegulatoryAction, Exposure, Prediction,
    EpidemiologyValidation, BradfordHillScore, LitigationScore,
    Defendant, PubMedPaper, LitigationStatus, UserAction
)
from scoring.bradford_hill import BradfordHillScorer
from scoring.litigation import LitigationScorer

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/ede')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="EDE API",
    description="Epidemiological Discovery Engine - Mass Tort Signal Detection",
    version="1.0.0"
)

# CORS middleware (allow frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Pydantic Models (Request/Response schemas)
# ============================================================================

class SignalListResponse(BaseModel):
    signal_id: str
    name: str
    chemical: str
    disease: str
    methodology: str
    status: str
    bradford_hill_score: Optional[Decimal]
    litigation_score: Optional[Decimal]
    market_size_min: Optional[int]
    market_size_max: Optional[int]
    date_detected: str
    is_pre_litigation: Optional[bool]

    class Config:
        from_attributes = True


class SignalDetailResponse(BaseModel):
    signal_id: str
    chemical: str
    disease: str
    methodology: str
    status: str
    bradford_hill_score: Optional[Decimal]
    litigation_score: Optional[Decimal]
    market_size_min: Optional[int]
    market_size_max: Optional[int]
    addressable_plaintiffs_min: Optional[int]
    addressable_plaintiffs_max: Optional[int]
    date_detected: str
    date_updated: str
    notes: Optional[str]
    # Related data
    regulatory_actions: List[dict]
    defendants: List[dict]
    bradford_hill_breakdown: Optional[dict]
    litigation_breakdown: Optional[dict]
    litigation_status: Optional[dict]

    class Config:
        from_attributes = True


class PortfolioResponse(BaseModel):
    validated_discoveries: int
    total_market_size_min: int
    total_market_size_max: int
    avg_bradford_hill: Decimal
    discoveries: List[SignalListResponse]

    class Config:
        from_attributes = True


class UserActionRequest(BaseModel):
    action_type: str  # ADD_TO_WATCHLIST, ARCHIVE, START_VALIDATION, etc.
    action_data: Optional[dict] = None


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
def root():
    """Health check"""
    return {"status": "ok", "message": "EDE API is running"}


@app.get("/api/signals", response_model=List[SignalListResponse])
def list_signals(
    status: Optional[str] = Query(None, description="Filter by status (DETECTED, READY_TO_VALIDATE, VALIDATED, etc.)"),
    bradford_hill_min: Optional[float] = Query(None, description="Minimum Bradford Hill score"),
    litigation_min: Optional[float] = Query(None, description="Minimum Litigation score"),
    methodology: Optional[str] = Query(None, description="Filter by methodology (HAZARD_FIRST, EPIDEMIOLOGY_FIRST)"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """
    List all signals with optional filtering

    Returns signals sorted by litigation score (highest first)
    """
    query = db.query(Signal)

    # Apply filters
    if status:
        query = query.filter(Signal.status == status)

    if bradford_hill_min is not None:
        query = query.filter(Signal.bradford_hill_score >= bradford_hill_min)

    if litigation_min is not None:
        query = query.filter(Signal.litigation_score >= litigation_min)

    if methodology:
        query = query.filter(Signal.methodology == methodology)

    # Sort by litigation score (descending)
    query = query.order_by(desc(Signal.litigation_score), desc(Signal.bradford_hill_score))

    # Pagination
    signals = query.limit(limit).offset(offset).all()

    # Join litigation status to get is_pre_litigation
    results = []
    for signal in signals:
        lit_status = db.query(LitigationStatus).filter(LitigationStatus.signal_id == signal.id).first()
        results.append(SignalListResponse(
            signal_id=signal.signal_id,
            name=f"{signal.chemical} → {signal.disease}",
            chemical=signal.chemical,
            disease=signal.disease,
            methodology=signal.methodology,
            status=signal.status,
            bradford_hill_score=signal.bradford_hill_score,
            litigation_score=signal.litigation_score,
            market_size_min=signal.market_size_min,
            market_size_max=signal.market_size_max,
            date_detected=str(signal.date_detected),
            is_pre_litigation=lit_status.is_pre_litigation if lit_status else None
        ))

    return results


@app.get("/api/signals/{signal_id}", response_model=SignalDetailResponse)
def get_signal_detail(signal_id: str, db: Session = Depends(get_db)):
    """
    Get detailed information for a specific signal

    Includes:
    - Bradford Hill breakdown (all 9 criteria)
    - Litigation breakdown (all 7 factors)
    - Regulatory actions
    - Defendants
    - Litigation status
    """
    signal = db.query(Signal).filter(Signal.signal_id == signal_id).first()

    if not signal:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

    # Fetch related data
    regulatory_actions = db.query(RegulatoryAction).filter(RegulatoryAction.signal_id == signal.id).all()
    defendants = db.query(Defendant).filter(Defendant.signal_id == signal.id).all()
    bradford_hill = db.query(BradfordHillScore).filter(BradfordHillScore.signal_id == signal.id).first()
    litigation = db.query(LitigationScore).filter(LitigationScore.signal_id == signal.id).first()
    lit_status = db.query(LitigationStatus).filter(LitigationStatus.signal_id == signal.id).first()

    # Format response
    return SignalDetailResponse(
        signal_id=signal.signal_id,
        chemical=signal.chemical,
        disease=signal.disease,
        methodology=signal.methodology,
        status=signal.status,
        bradford_hill_score=signal.bradford_hill_score,
        litigation_score=signal.litigation_score,
        market_size_min=signal.market_size_min,
        market_size_max=signal.market_size_max,
        addressable_plaintiffs_min=signal.addressable_plaintiffs_min,
        addressable_plaintiffs_max=signal.addressable_plaintiffs_max,
        date_detected=str(signal.date_detected),
        date_updated=str(signal.date_updated),
        notes=signal.notes,
        regulatory_actions=[
            {
                'action_type': r.action_type,
                'agency': r.agency,
                'jurisdiction': r.jurisdiction,
                'action_date': str(r.action_date),
                'basis': r.basis,
                'regulatory_divergence': r.regulatory_divergence
            }
            for r in regulatory_actions
        ],
        defendants=[
            {
                'company_name': d.company_name,
                'annual_revenue': d.annual_revenue,
                'market_cap': d.market_cap,
                'is_public': d.is_public
            }
            for d in defendants
        ],
        bradford_hill_breakdown={
            'composite_score': float(bradford_hill.composite_score),
            'interpretation': bradford_hill.interpretation,
            'criteria': bradford_hill.evidence if bradford_hill.evidence else {}
        } if bradford_hill else None,
        litigation_breakdown={
            'composite_score': float(litigation.composite_score),
            'interpretation': litigation.interpretation,
            'factors': litigation.evidence if litigation.evidence else {}
        } if litigation else None,
        litigation_status={
            'pacer_cases_count': lit_status.pacer_cases_count,
            'mdl_status': lit_status.mdl_status,
            'media_coverage_count': lit_status.media_coverage_count,
            'is_pre_litigation': lit_status.is_pre_litigation
        } if lit_status else None
    )


@app.get("/api/portfolio", response_model=PortfolioResponse)
def get_portfolio(db: Session = Depends(get_db)):
    """
    Get portfolio view (validated discoveries only)

    Returns:
    - Count of validated discoveries
    - Combined market size
    - Average Bradford Hill score
    - List of discoveries
    """
    # Query validated and field-tested signals
    signals = db.query(Signal).filter(
        Signal.status.in_(['VALIDATED', 'FIELD_TESTED'])
    ).order_by(desc(Signal.litigation_score)).all()

    if not signals:
        return PortfolioResponse(
            validated_discoveries=0,
            total_market_size_min=0,
            total_market_size_max=0,
            avg_bradford_hill=Decimal('0'),
            discoveries=[]
        )

    # Calculate aggregates
    total_market_min = sum(s.market_size_min or 0 for s in signals)
    total_market_max = sum(s.market_size_max or 0 for s in signals)
    avg_bh = sum(float(s.bradford_hill_score or 0) for s in signals) / len(signals)

    # Format discoveries
    discoveries = []
    for signal in signals:
        lit_status = db.query(LitigationStatus).filter(LitigationStatus.signal_id == signal.id).first()
        discoveries.append(SignalListResponse(
            signal_id=signal.signal_id,
            name=f"{signal.chemical} → {signal.disease}",
            chemical=signal.chemical,
            disease=signal.disease,
            methodology=signal.methodology,
            status=signal.status,
            bradford_hill_score=signal.bradford_hill_score,
            litigation_score=signal.litigation_score,
            market_size_min=signal.market_size_min,
            market_size_max=signal.market_size_max,
            date_detected=str(signal.date_detected),
            is_pre_litigation=lit_status.is_pre_litigation if lit_status else None
        ))

    return PortfolioResponse(
        validated_discoveries=len(signals),
        total_market_size_min=total_market_min,
        total_market_size_max=total_market_max,
        avg_bradford_hill=Decimal(str(round(avg_bh, 1))),
        discoveries=discoveries
    )


@app.post("/api/signals/{signal_id}/actions")
def create_user_action(signal_id: str, action: UserActionRequest, db: Session = Depends(get_db)):
    """
    Record a user action on a signal

    Actions:
    - ADD_TO_WATCHLIST
    - REMOVE_FROM_WATCHLIST
    - START_VALIDATION
    - ARCHIVE
    - DOWNLOAD_DOSSIER
    - ADD_NOTE
    """
    signal = db.query(Signal).filter(Signal.signal_id == signal_id).first()

    if not signal:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

    # Create user action record
    user_action = UserAction(
        signal_id=signal.id,
        action_type=action.action_type,
        action_data=action.action_data
    )
    db.add(user_action)

    # Update signal status if needed
    if action.action_type == 'START_VALIDATION':
        signal.status = 'IN_VALIDATION'
    elif action.action_type == 'ARCHIVE':
        signal.status = 'ARCHIVED'
        signal.archive_reason = action.action_data.get('reason') if action.action_data else None

    db.commit()

    return {"status": "ok", "message": f"Action {action.action_type} recorded"}


@app.get("/api/pipeline")
def get_signal_pipeline(db: Session = Depends(get_db)):
    """
    Get signal pipeline statistics (for dashboard funnel visualization)

    Returns counts for each status
    """
    from sqlalchemy import func

    pipeline = db.query(
        Signal.status,
        func.count(Signal.id).label('count'),
        func.avg(Signal.bradford_hill_score).label('avg_bradford_hill'),
        func.avg(Signal.litigation_score).label('avg_litigation')
    ).filter(
        Signal.status != 'ARCHIVED'
    ).group_by(Signal.status).all()

    results = []
    for status, count, avg_bh, avg_lit in pipeline:
        results.append({
            'status': status,
            'count': count,
            'avg_bradford_hill': float(avg_bh) if avg_bh else 0,
            'avg_litigation': float(avg_lit) if avg_lit else 0
        })

    return results


@app.get("/api/signals/{signal_id}/dossier.pdf")
def generate_dossier(signal_id: str, db: Session = Depends(get_db)):
    """
    Generate discovery dossier PDF

    TODO: Implement PDF generation using WeasyPrint or ReportLab
    """
    signal = db.query(Signal).filter(Signal.signal_id == signal_id).first()

    if not signal:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

    # TODO: Generate PDF
    # For now, return placeholder
    return {
        "status": "pending",
        "message": "PDF generation not yet implemented",
        "signal_id": signal_id
    }


# ============================================================================
# Development/Testing Endpoints
# ============================================================================

@app.post("/api/dev/score-signal/{signal_id}")
def score_signal(signal_id: str, db: Session = Depends(get_db)):
    """
    Development endpoint to manually trigger scoring for a signal

    This would normally be done automatically by the regulatory/epidemiology scanners
    """
    signal = db.query(Signal).filter(Signal.signal_id == signal_id).first()

    if not signal:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

    # Gather data for scoring (simplified for now)
    # In production, this would query PubMed, SEER, etc.
    signal_data = {
        'chemical': signal.chemical,
        'disease': signal.disease,
        # TODO: Fetch real data from exposures, predictions, validations tables
    }

    # Score Bradford Hill
    bh_scorer = BradfordHillScorer()
    # bh_result = bh_scorer.score(signal_data)  # TODO: Need to populate signal_data

    # Score Litigation
    lit_scorer = LitigationScorer()
    # lit_result = lit_scorer.score(signal_data, bh_result.composite_score)

    return {
        "status": "ok",
        "message": "Scoring not yet fully implemented (needs PubMed/SEER integration)",
        "signal_id": signal_id
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
