.PHONY: install dev setup-db discovery fda-discovery full-discovery test lint clean help

# Default target
help:
	@echo "TortSignal - Available commands:"
	@echo ""
	@echo "  Setup:"
	@echo "    make install     Install production dependencies"
	@echo "    make dev         Install dev dependencies"
	@echo "    make setup-db    Initialize database schema"
	@echo ""
	@echo "  Discovery Mode:"
	@echo "    make fda-discovery      Run FDA discovery (FAERS + MAUDE)"
	@echo "    make fda-discovery-dry  FDA discovery without database writes"
	@echo "    make court-discovery    Run court filing discovery"
	@echo "    make full-discovery     Run all discovery pipelines"
	@echo ""
	@echo "  Development:"
	@echo "    make test        Run tests"
	@echo "    make lint        Run linter"
	@echo "    make health-check Check connector health"
	@echo "    make top-candidates Show top candidates from database"
	@echo ""
	@echo "Environment:"
	@echo "  Copy .env.example to .env and fill in your values"

# Install production dependencies
install:
	pip install -e .

# Install dev dependencies
dev:
	pip install -e ".[dev]"

# Initialize database
setup-db:
	@echo "Creating database schema..."
	psql $(DATABASE_URL) < schema/001_core.sql
	@echo "Done."

# =============================================================================
# DISCOVERY MODE - The core value proposition
# =============================================================================

# Run FDA discovery (FAERS drugs + MAUDE devices)
fda-discovery:
	@echo "Running FDA Discovery (FAERS + MAUDE)..."
	python -m src.pipeline.fda_discovery --current-days 30 --baseline-days 365

# FDA discovery without database writes (for testing)
fda-discovery-dry:
	@echo "Running FDA Discovery (dry run)..."
	python -m src.pipeline.fda_discovery --current-days 30 --baseline-days 365 --no-persist

# FDA discovery with JSON output
fda-discovery-json:
	@echo "Running FDA Discovery with JSON output..."
	python -m src.pipeline.fda_discovery --current-days 30 --baseline-days 365 --output discovery_results.json
	@echo "Results written to discovery_results.json"

# Run court filing discovery (requires UniCourt implementation)
court-discovery:
	python -m src.pipeline.discovery --days 7 --limit 100

# Run court discovery in dry-run mode
court-discovery-dry:
	python -m src.pipeline.discovery --days 7 --limit 100 --dry-run

# Run ALL discovery pipelines
full-discovery: fda-discovery court-discovery
	@echo ""
	@echo "Full discovery complete!"
	@echo "Run 'make top-candidates' to see results"

# =============================================================================
# DEVELOPMENT & TESTING
# =============================================================================

# Run tests
test:
	pytest tests/ -v

# Run linter
lint:
	ruff check src/ tests/
	mypy src/

# Format code
format:
	ruff format src/ tests/

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Show top candidates from database
top-candidates:
	@psql $(DATABASE_URL) -c "SELECT defendant_text, product_text, score_total, category, status FROM candidates WHERE status != 'rejected' ORDER BY score_total DESC LIMIT 20;"

# Show recent signals
recent-signals:
	@psql $(DATABASE_URL) -c "SELECT event_type, snippet, detected_at FROM signal_events ORDER BY detected_at DESC LIMIT 20;"

# Health check for connectors
health-check:
	@echo "Checking connector health..."
	@python -c "from src.connectors.faers import FAERSConnector; print('FAERS:', 'OK' if FAERSConnector().health_check() else 'FAIL')"
	@python -c "from src.connectors.maude import MAUDEConnector; print('MAUDE:', 'OK' if MAUDEConnector().health_check() else 'FAIL')"
	@python -c "from src.connectors.pubmed import PubMedConnector; print('PubMed:', 'OK' if PubMedConnector().health_check() else 'FAIL')"
	@echo "Done."

# Quick test of FAERS discovery (useful for development)
test-faers:
	@python -c "from src.connectors.faers import FAERSConnector; c = FAERSConnector(); print('Top 10 drugs (last 30d):'); [print(f\"  {d['drug_name']}: {d['count']}\") for d in c.get_trending_drugs(days=30, top_n=10)]"

# Quick test of MAUDE discovery
test-maude:
	@python -c "from src.connectors.maude import MAUDEConnector; c = MAUDEConnector(); print('Top 10 devices (last 30d):'); [print(f\"  {d['device_name']}: {d['count']}\") for d in c.get_trending_devices(days=30, top_n=10)]"
