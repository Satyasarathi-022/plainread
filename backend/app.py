"""
PlainRead — Lambda handler

Combines two of the hackathon's open-theme prompts into one project:
  - Idea #1 (document explainer agent): breaks a rental agreement into
    plain-language meaning, key numbers/dates, and clauses worth a second
    look.
  - Idea #4 (local-language interface), folded in as a bonus feature: the
    `language` field below is sent straight into the Bedrock prompt, so the
    explanation is *generated* in the reader's language (Hindi, Bengali,
    Tamil, Telugu, Marathi, Kannada, or English), not machine-translated
    after the fact.

Receives rental-agreement text + a target language, asks a Bedrock foundation
model to break it into plain language, and returns structured JSON that the
frontend renders as three blocks: meaning, key numbers/dates, and clauses
worth a second look.
"""

import json
import os
import re
import boto3

REGION = os.environ.get("BEDROCK_REGION", "ap-south-1")
# Amazon's own Nova models are billed directly by AWS, not through a
# third-party AWS Marketplace subscription like Anthropic's models are.
# If your account hits an AWS Marketplace payment-instrument error trying
# to invoke Claude, switching to a Nova model sidesteps that entirely.
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")

bedrock = boto3.client("bedrock-runtime", region_name=REGION)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "OPTIONS,POST",
}

SYSTEM_PROMPT = """You are PlainRead, an assistant that explains legal documents \
(rental agreements, in particular) to people with no legal background.

Given the raw text of a rental agreement, respond with STRICT JSON only, no \
markdown fences, no commentary, matching this exact shape:

{
  "meaning": "2-4 sentence plain-language summary of what this agreement is and what it commits the tenant to.",
  "key_numbers": ["short bullet with a number or date and what it means", "..."],
  "watch_out": ["short bullet describing an unusual, one-sided, or risky clause, and why it matters", "..."]
}

Rules:
- [Idea #4 — local-language interface] Write the "meaning", "key_numbers", \
and "watch_out" content in the language the user requests, even though \
these field names stay in English. Generate the explanation natively in \
that language rather than writing it in English and translating.
- key_numbers should cover things like rent amount, security deposit, lock-in \
period, notice period, maintenance charges, and payment due dates -- only \
include ones actually present in the text.
- watch_out should flag clauses that are unusual, vague, one-sided, or \
commonly disputed (e.g. non-refundable deposits, unilateral rent hikes, \
broad eviction clauses, unclear maintenance responsibility). If nothing \
stands out, return an empty list.
- Keep each bullet under 30 words.
- Never invent numbers or clauses that are not in the text.
- Output must be valid JSON and nothing else.
"""


def _extract_json(raw_text: str) -> dict:
    """Bedrock models sometimes wrap JSON in prose or code fences; pull the
    JSON object out defensively."""
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model response")
    return json.loads(match.group(0))


def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    try:
        body = json.loads(event.get("body") or "{}")
        document_text = (body.get("document_text") or "").strip()
        language = (body.get("language") or "English").strip()

        if not document_text:
            return _response(400, {"error": "document_text is required"})

        # Keep prompts within a sane size for a hackathon demo.
        document_text = document_text[:12000]

        user_prompt = (
            f"Target language for the explanation: {language}\n\n"
            f"Rental agreement text:\n---\n{document_text}\n---"
        )

        bedrock_request = {
            "modelId": MODEL_ID,
            "system": [{"text": SYSTEM_PROMPT}],
            "messages": [
                {"role": "user", "content": [{"text": user_prompt}]}
            ],
            "inferenceConfig": {"maxTokens": 1200},
        }

        response = bedrock.converse(**bedrock_request)

        raw_text = response["output"]["message"]["content"][0]["text"]
        result = _extract_json(raw_text)

        return _response(200, {
            "meaning": result.get("meaning", ""),
            "key_numbers": result.get("key_numbers", []),
            "watch_out": result.get("watch_out", []),
        })

    except Exception as exc:  # noqa: BLE001 - keep the demo resilient
        return _response(500, {"error": str(exc)})


def _response(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
        "body": json.dumps(body),
    }
