# TortSignal Data Contracts

This document defines the data contracts (schemas) for each connector. All connectors follow a consistent pattern:

1. **Ingest envelope**: Common wrapper with provenance metadata
2. **Source-specific payload**: The actual data from the source
3. **Normalized outputs**: SourceDocument, EntityMentions, SignalEvents

---

## Global Contract: Ingest Envelope

Every connector emits the same outer envelope:

```json
{
  "schema_version": "1.0",
  "source": "court|faers|maude|pubmed|semantic_scholar|edgar",
  "source_type": "court_case|faers_report|maude_report|pubmed_article|sec_filing",
  "source_uid": "string-stable-upstream-id",
  "retrieved_at": "2026-01-18T12:34:56Z",
  "published_at": "2024-11-03T00:00:00Z",
  "url": "https://...",
  "raw": {
    "blob_uri": "s3://.../raw/....json.gz",
    "sha256": "hex-string",
    "content_type": "application/json",
    "byte_length": 12345
  },
  "provenance": {
    "connector_version": "unicourt@0.3.1",
    "ingest_run_id": "uuid",
    "license_tier": "unicourt_pro|public",
    "rate_limit_bucket": "string"
  },
  "payload": { }
}
```

**Idempotency key**: `(source_type, source_uid, raw.sha256)`

---

## Global Contract: Normalized Outputs

### SourceDocument

Maps 1:1 to the `source_documents` table:

```json
{
  "doc": {
    "source_type": "pubmed",
    "source_uid": "PMID:12345678",
    "title": "string",
    "published_at": "2024-10-12T00:00:00Z",
    "retrieved_at": "2026-01-18T12:34:56Z",
    "url": "https://...",
    "raw_blob_uri": "s3://...",
    "raw_hash_sha256": "hex",
    "metadata": { }
  }
}
```

### Entity Mentions

Extracted entities before resolution:

```json
{
  "entity_mentions": [
    {
      "entity_type": "defendant|product|injury",
      "mention_text": "Roundup",
      "normalized_entity_id": "uuid-or-null",
      "resolution_method": "rules|ner|hybrid|manual",
      "confidence": 0.91,
      "span": { "start": 120, "end": 126 },
      "context_snippet": "..."
    }
  ]
}
```

### SignalEvent

Maps to the `signal_events` table:

```json
{
  "events": [
    {
      "event_type": "filing_new|filing_spike|adverse_trend|paper_published|meta_analysis|sec_language_delta",
      "event_time": "2024-10-12T00:00:00Z",
      "cluster_ref": {
        "defendant_id": "uuid-or-null",
        "product_id": "uuid-or-null",
        "injury_id": "uuid-or-null",
        "cluster_id": "uuid-or-null"
      },
      "weight": 0.0,
      "features": { },
      "excerpt": "short human-readable evidence",
      "doc_source_uid": "string",
      "doc_id": "uuid-or-null"
    }
  ]
}
```

---

## Court Filings (UniCourt / PACER)

### Court Case Payload

`source_type`: `court_case`

```json
{
  "case": {
    "upstream_case_id": "UNICOURT:abc123",
    "docket_number": "1:24-cv-00001",
    "court": {
      "name": "U.S. District Court for the Southern District of Texas",
      "jurisdiction": "federal",
      "district_or_county": "Southern District",
      "state": "TX"
    },
    "filed_date": "2024-06-01",
    "case_type": "Product Liability",
    "nature_of_suit": "365",
    "judge": "Judge Name",
    "status": "open",
    "parties": [
      {
        "name": "Plaintiff Name",
        "side": "plaintiff",
        "party_type": "individual"
      },
      {
        "name": "Bayer Corporation",
        "side": "defendant",
        "party_type": "company"
      }
    ],
    "attorneys": [
      {
        "name": "Attorney Name",
        "side": "plaintiff",
        "firm": "Firm Name LLP"
      }
    ],
    "claims_text": "Plaintiff alleges...",
    "product_mentions": ["Roundup", "glyphosate"],
    "injury_mentions": ["non-Hodgkin lymphoma"],
    "links": {
      "docket_url": "https://...",
      "complaint_url": "https://..."
    }
  }
}
```

**Required fields**: `upstream_case_id`, `court`, `filed_date`, `parties` (at least one defendant)

### Derived Events

- `filing_new`: One per case
- `filing_spike`: Per cluster per time window
  ```json
  {
    "event_type": "filing_spike",
    "features": {
      "cases_7d": 15,
      "cases_28d": 32,
      "acceleration": 2.1,
      "jurisdictions": 4,
      "plaintiff_firms": 8
    }
  }
  ```

---

## FDA FAERS (Drug Adverse Events)

### FAERS Report Payload

`source_type`: `faers_report`

```json
{
  "faers_report": {
    "primaryid": "123456789",
    "caseid": "12345678",
    "case_version": "1",
    "receivedate": "20240615",
    "event_dt": "20240601",
    "reporter_country": "US",
    "patient": {
      "sex": "F",
      "age_yrs": 45
    },
    "drugs": [
      {
        "drugname": "OZEMPIC",
        "prod_ai": "semaglutide",
        "role_cod": "PS",
        "route": "subcutaneous",
        "dose_vbm": "0.5mg weekly"
      }
    ],
    "reactions": [
      { "reac_pt": "Gastroparesis" },
      { "reac_pt": "Nausea" }
    ],
    "outcomes": [
      { "outc_cod": "HO" }
    ],
    "source_fileset": "2024Q3",
    "notes": {
      "narrative": "Patient developed..."
    }
  }
}
```

**Role codes**: PS (Primary Suspect), SS (Secondary Suspect), C (Concomitant), I (Interacting)

**Outcome codes**: DE (Death), LT (Life-threatening), HO (Hospitalization), DS (Disability), CA (Congenital Anomaly), RI (Required Intervention), OT (Other)

### Derived Events

```json
{
  "event_type": "adverse_trend",
  "features": {
    "source": "faers",
    "drug_name": "OZEMPIC",
    "window_days": 180,
    "reports_current": 450,
    "reports_baseline": 120,
    "delta_pct": 275,
    "prr_proxy": 2.8,
    "top_reactions": ["Gastroparesis", "Ileus", "Intestinal obstruction"]
  }
}
```

---

## FDA MAUDE (Device Adverse Events)

### MAUDE Report Payload

`source_type`: `maude_report`

```json
{
  "maude_report": {
    "mdr_report_key": "12345678",
    "event_type": "Injury",
    "report_date": "2024-06-15",
    "manufacturer": "Boston Scientific",
    "brand_name": "Mesh Product Name",
    "device": {
      "product_code": "OTN",
      "device_problem_codes": ["1546", "2993"],
      "generic_name": "Surgical Mesh",
      "model_number": "ABC123"
    },
    "patient": {
      "age": "52",
      "sex": "F"
    },
    "text": {
      "event_description": "Patient experienced mesh erosion...",
      "manufacturer_narrative": "Investigation ongoing..."
    },
    "links": {
      "report_url": "https://..."
    }
  }
}
```

### Derived Events

Same structure as FAERS `adverse_trend`, with `source: "maude"` and device-specific fields.

---

## PubMed (Scientific Literature)

### PubMed Article Payload

`source_type`: `pubmed_article`

```json
{
  "pubmed_article": {
    "pmid": "12345678",
    "doi": "10.1000/example",
    "title": "Association between glyphosate exposure and non-Hodgkin lymphoma: a meta-analysis",
    "abstract": "Background: Several studies have...",
    "journal": "International Journal of Cancer",
    "pub_date": "2024-03-15",
    "publication_types": ["Meta-Analysis", "Review"],
    "authors": [
      {
        "name": "Smith J",
        "affiliation": "University of California"
      }
    ],
    "mesh_terms": [
      "Glyphosate/adverse effects",
      "Lymphoma, Non-Hodgkin/chemically induced"
    ],
    "chemicals": ["Glyphosate"],
    "keywords": ["herbicide", "cancer risk", "epidemiology"],
    "links": {
      "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
      "pmc_url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC..."
    }
  }
}
```

### Derived Events

```json
{
  "event_type": "paper_published",
  "features": {
    "pmid": "12345678",
    "journal": "International Journal of Cancer",
    "pub_types": ["Meta-Analysis"],
    "is_meta_analysis": true,
    "mesh_terms": ["..."],
    "weight_multiplier": 3.0
  }
}
```

For meta-analyses specifically:

```json
{
  "event_type": "meta_analysis",
  "features": {
    "pmid": "12345678",
    "title": "...",
    "journal": "...",
    "finding_direction": "positive_association",
    "effect_size": "OR 1.41",
    "confidence_interval": "1.13-1.75"
  }
}
```

---

## Semantic Scholar (Paper Graph)

### S2 Paper Payload

`source_type`: `s2_paper`

```json
{
  "s2_paper": {
    "paperId": "abc123def456",
    "externalIds": {
      "DOI": "10.1000/example",
      "PubMed": "12345678"
    },
    "title": "...",
    "abstract": "...",
    "year": 2024,
    "venue": "Nature Medicine",
    "fieldsOfStudy": ["Medicine", "Biology"],
    "citationCount": 123,
    "influentialCitationCount": 12,
    "authors": [
      {
        "name": "Smith J",
        "authorId": "12345"
      }
    ],
    "references": [
      { "paperId": "ref123" }
    ],
    "citations": [
      { "paperId": "cite456" }
    ]
  }
}
```

**Usage**: Primarily for enriching PubMed records with citation counts and influence metrics. Dedupe against PubMed via DOI/PMID.

---

## SEC EDGAR (Corporate Filings)

### SEC Filing Payload

`source_type`: `sec_filing`

```json
{
  "sec_filing": {
    "accession": "0000123456-24-000789",
    "cik": "0000123456",
    "company_name": "Bayer AG",
    "ticker": "BAYRY",
    "form_type": "10-Q",
    "filing_date": "2024-11-05",
    "period_of_report": "2024-09-30",
    "sections": {
      "legal_proceedings_text": "The Company is currently a defendant in approximately 170,000 lawsuits...",
      "risk_factors_text": "We face significant litigation risk related to our crop science products...",
      "contingencies_text": "We have accrued $5.2 billion for Roundup-related litigation..."
    },
    "extracted_amounts": [
      {
        "label": "litigation_reserve",
        "amount_usd": 5200000000,
        "confidence": 0.85,
        "evidence_span": { "start": 1002, "end": 1044 }
      }
    ],
    "links": {
      "filing_url": "https://www.sec.gov/Archives/edgar/...",
      "primary_doc_url": "https://..."
    }
  }
}
```

### Derived Events

**Language delta** (compare current vs previous quarter):

```json
{
  "event_type": "sec_language_delta",
  "features": {
    "compare_to_accession": "0000123456-24-000123",
    "section": "legal_proceedings",
    "delta_method": "semantic+lexical",
    "delta_score": 0.83,
    "new_phrases": ["reasonably possible loss", "material adverse effect", "class action"],
    "removed_phrases": []
  },
  "excerpt": "New language suggests increased expected loss exposure..."
}
```

**Reserve delta**:

```json
{
  "event_type": "sec_reserve_delta",
  "features": {
    "amount_usd": 5200000000,
    "prev_amount_usd": 4800000000,
    "delta_usd": 400000000,
    "delta_pct": 8.3,
    "confidence": 0.85
  },
  "excerpt": "Litigation reserve increased by $400M (8.3%) quarter-over-quarter"
}
```

---

## Cluster Linkage Contract

Output from the entity resolution / cluster linking job:

```json
{
  "cluster_linkage": {
    "doc_source_uid": "PMID:12345678",
    "candidates": [
      {
        "defendant_id": "uuid-or-null",
        "product_id": "uuid-or-null",
        "injury_id": "uuid-or-null",
        "confidence": 0.77,
        "reasons": ["product_alias_match", "injury_mesh_match", "defendant_in_text"],
        "proposed_category": "chemical"
      }
    ]
  }
}
```

This job populates:
- `entity_aliases` (as new synonyms are learned)
- `tort_clusters` (create if not exists)
- `case_cluster_map` (for court filings)
- `signal_events.cluster_id` (backfill)

---

## Validation Rules

### All Connectors

- Must provide: `schema_version`, `source`, `source_type`, `source_uid`, `retrieved_at`, `raw.sha256`
- Date formats: RFC3339 for timestamps, ISO YYYY-MM-DD for date-only fields
- Payload must be JSON-serializable
- No silent drops: if parsing fails, emit an `ingest_error` record

### PII Handling

- Raw narratives (FAERS, MAUDE) may contain PII
- Store raw with restricted access
- Excerpts shown in UI should be scrubbed or anonymized

---

## OpenFDA API Reference

### FAERS Endpoint

```
GET https://api.fda.gov/drug/event.json
```

**Query parameters**:
- `search`: Field queries (e.g., `patient.drug.openfda.brand_name:"OZEMPIC"`)
- `count`: Aggregate field (e.g., `count=patient.reaction.reactionmeddrapt.exact`)
- `limit`: Results per page (max 1000)

**Date filtering**:
```
search=receivedate:[20240101+TO+20240630]
```

### MAUDE Endpoint

```
GET https://api.fda.gov/device/event.json
```

Same query pattern as FAERS.

**Documentation**: https://open.fda.gov/apis/

---

## API Rate Limits

| Source | Rate Limit | Strategy |
|--------|-----------|----------|
| OpenFDA | 240/min (with key), 40/min (without) | Request API key, implement backoff |
| PubMed E-utilities | 3/sec (without key), 10/sec (with) | Request API key |
| SEC EDGAR | 10 req/sec | Respect headers, implement backoff |
| UniCourt | Per contract | Check your sandbox limits |

---

## Implementation Priority

1. **UniCourt** — Primary discovery source (you have access)
2. **OpenFDA FAERS** — Free, high signal for pharma
3. **OpenFDA MAUDE** — Free, high signal for devices
4. **PubMed** — Free, adds scientific plausibility
5. **SEC EDGAR** — Free, adds "issuer awareness" signal (Phase 5)
