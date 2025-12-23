#!/usr/bin/env python3
"""Test script to run BOQ extraction and display results."""

import sys
import json

sys.path.insert(0, '/Users/shumaelr/RealCode/Enquiry/automation_script')

from extractors import extract_pdf_text
from llm_client import process_with_claude

pdf_path = "/Users/shumaelr/RealCode/Enquiry/2025.11.29R to Shumael - AI - BOQ, Sizing & SLD/BOQ/01_Scope Of Supply.pdf"

print("\n" + "="*60)
print("BOQ EXTRACTION TEST")
print("="*60)

print("\n[1] Extracting PDF text...")
pdf_text = extract_pdf_text(pdf_path)
print(f"✅ Extracted {len(pdf_text)} characters from PDF\n")

print("[2] Calling Claude API (30-45 seconds)...")
result = process_with_claude(pdf_text, "", category="BOQ")

if result:
    print("\n" + "="*60)
    print("✅ EXTRACTED BOQ DATA")
    print("="*60 + "\n")
    print(json.dumps(result, indent=2))
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
else:
    print("❌ No result returned from Claude")
    sys.exit(1)
