"""
Takes raw articles saved by fetch_rss.py and uses Claude to pull out
structured funding round data — including the deeper science/investor
context (what the company is working on, who's leading the round and why).

This is the step that turns "TechCrunch: Acme Biotech raises $40M Series B
led by ARCH Venture to advance its in vivo CAR-T pipeline for lupus" into:
  company: Acme Biotech
  stage: Series B
  amount_usd_millions: 40
  modality: In vivo CAR-T
  target_indication: Lupus
  lead_investor: ARCH Venture
  lead_investor_type: Specialist VC
"""
import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic
from db import get_connection, init_db

load_dotenv()

client = Anthropic(api_key=(os.environ.get("ANTHROPIC_API_KEY") or "").strip())

EXTRACTION_PROMPT = """You are extracting structured funding round data from a news article snippet, for a biotech/healthtech investor tracking tool.

Title: {title}
Summary: {summary}

If this article describes a specific company raising a specific equity funding round (seed, Series A/B/C/D+, growth, or similar), extract the details below.

If it is NOT about a specific funding round (e.g. it's about clinical trial results, FDA approval, M&A/acquisitions, layoffs, or a vague industry trend piece), respond with exactly: {{"is_funding_round": false}}

Otherwise respond with ONLY this JSON object, no other text:
{{
  "is_funding_round": true,
  "company": "company name",
  "stage": "Seed | Series A | Series B | Series C | Series D+ | Growth | Debt | Grant | Other",
  "amount_usd_millions": <number, or null if not stated>,
  "sector": "short sector label, e.g. 'Cell therapy', 'Gene editing', 'Digital health', 'AI drug discovery', 'Diagnostics', 'Medical device'",
  "modality": "the specific scientific/technical approach if this is a therapeutics company, e.g. 'In vivo CAR-T', 'Allogeneic CAR-T', 'AAV gene therapy', 'mRNA', 'Antibody-drug conjugate', 'Small molecule', 'Digital therapeutic'. Use null if not applicable (e.g. a pure software/digital health company with no therapeutic modality).",
  "target_indication": "the disease/condition being targeted, e.g. 'B-cell lymphoma', 'Duchenne muscular dystrophy', 'Type 2 diabetes'. Null if not stated or not applicable.",
  "trial_phase": "Preclinical | Phase 1 | Phase 2 | Phase 3 | Approved | Not applicable | Not stated",
  "mechanism_summary": "1-2 plain-English sentences on what the company is actually trying to achieve scientifically or clinically — written for someone who knows the industry but wants the specific hook of THIS company, not generic boilerplate.",
  "location": "city, state/country if mentioned, else null",
  "lead_investor": "lead investor name if stated, else null",
  "lead_investor_type": "Specialist VC | Corporate Strategic | Growth/Generalist | Government/Nonprofit | Undisclosed — classify based on the investor named. Corporate Strategic means a pharma/biotech company's venture arm (e.g. Eli Lilly, GV, Novartis Venture Fund, Amgen Ventures, J&J Innovation). Specialist VC means a dedicated life-science fund (e.g. ARCH Venture, RA Capital, Third Rock, Flagship, Polaris).",
  "lead_investor_rationale":
