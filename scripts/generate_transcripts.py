#!/usr/bin/env python3
"""
Generate realistic banking customer service call transcripts as CSVs
for ingestion into the embedding-demo app.

Uses any OpenAI-compatible API (NanoGPT, Ollama, vLLM, LM Studio, etc.).

Usage:
    # NanoGPT (default)
    python scripts/generate_transcripts.py --api-key YOUR_KEY --num-transcripts 20

    # Local Ollama
    python scripts/generate_transcripts.py --base-url http://localhost:11434/v1 --model llama3 --num-transcripts 10

    # LM Studio
    python scripts/generate_transcripts.py --base-url http://localhost:1234/v1 --model local-model --num-transcripts 5
"""

import argparse
import csv
import json
import os
import random
import string
import sys
import time
from datetime import date, timedelta

import requests

DEFAULT_BASE_URL = "https://nano-gpt.com/api/v1"

SYSTEM_PROMPT = """\
You are a transcript generator for a UK banking customer service call centre.
Generate a single realistic phone call transcript between an AGENT and a CUSTOMER.

Rules:
- The call should be 25-40 exchanges (sentences) long.
- Each line must be prefixed with either "Agent:" or "Customer:".
- Use natural, conversational British English.
- Include realistic banking details: sort codes, partial account references, product names (current accounts, ISAs, mortgages, overdrafts, credit cards, savings accounts, direct debits, standing orders).
- Vary the tone: some customers are frustrated, some confused, some polite, some in financial difficulty.
- Include typical call flow: greeting, identity verification, issue discussion, resolution/escalation, closing.
- Do NOT include any commentary, headers, or markdown — output ONLY the transcript lines, one per line.
"""

SCENARIOS = [
    "The customer is calling to dispute an unrecognised transaction on their current account.",
    "The customer wants to increase their overdraft limit because they are struggling with bills.",
    "The customer is complaining about being charged fees they don't understand.",
    "The customer wants to close their account and move to another bank.",
    "The customer is asking about mortgage rates and wants to remortgage.",
    "The customer has been a victim of a phishing scam and needs to report fraud.",
    "The customer wants to set up a direct debit for a new utility bill.",
    "The customer is calling because their debit card has been declined abroad.",
    "The customer wants to open a Junior ISA for their child.",
    "The customer is in financial hardship and is asking for a payment holiday on their loan.",
    "The customer is upset because a standing order was sent to the wrong account.",
    "The customer is enquiring about switching their current account using the switching service.",
    "The customer wants to add their partner as a joint account holder.",
    "The customer is confused about interest rates on their savings account dropping.",
    "The customer needs to update their address and phone number after moving house.",
    "The customer received a letter about their credit card limit being reduced and wants to appeal.",
    "The customer is asking why a cheque they deposited hasn't cleared yet.",
    "The customer is calling to make a formal complaint about branch staff behaviour.",
    "The customer wants help setting up mobile banking and is not tech-savvy.",
    "The customer is worried about suspicious texts claiming to be from the bank.",
    "The customer wants to cancel a recurring card payment to a subscription service.",
    "The customer needs an emergency replacement card before travelling tomorrow.",
    "The customer is asking about bereavement — they need to notify the bank of a family member's death.",
    "The customer wants to understand PPI refund letters they received.",
    "The customer is calling about a bounce-back loan repayment they can't afford.",
]

TONES = ["angry",
         "frustrated",
         "polite",
         "in financial difficulty",
         "scared",
         "happy",
         "normal",
         "sad",
         "normal",
         "polite"
        ]


def stream_chat_completion(api_key: str, messages: list, model: str, base_url: str):
    """Send a streaming chat completion request and yield content chunks."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    data = {
        "model": model,
        "messages": messages,
        "stream": True,
    }

    response = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=data,
        stream=True,
    )

    if response.status_code != 200:
        raise Exception(
            f"API error {response.status_code}: {response.text[:300]}"
        )

    for line in response.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                line = line[6:]
            if line == "[DONE]":
                break
            try:
                chunk = json.loads(line)
                if chunk["choices"][0]["delta"].get("content"):
                    yield chunk["choices"][0]["delta"]["content"]
            except json.JSONDecodeError:
                continue


def generate_transcript(api_key: str, scenario: str, model: str, base_url: str, tone: str) -> list[str]:
    """Generate a single transcript and return a list of sentences."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Generate a transcript for this scenario:\n{scenario}. Assume the customer has a tone: {tone}"},
    ]

    full_text = ""
    for chunk in stream_chat_completion(api_key, messages, model, base_url):
        full_text += chunk

    # Parse lines — keep only those starting with Agent: or Customer:
    lines = []
    for raw_line in full_text.strip().splitlines():
        raw_line = raw_line.strip()
        if raw_line.startswith("Agent:") or raw_line.startswith("Customer:"):
            lines.append(raw_line)

    return lines


def main():
    parser = argparse.ArgumentParser(
        description="Generate banking customer service transcript CSVs."
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"API base URL (default: {DEFAULT_BASE_URL}). For Ollama: http://localhost:11434/v1",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("NANOGPT_API_KEY"),
        help="API key (or set NANOGPT_API_KEY env var). For Ollama use any non-empty string.",
    )
    parser.add_argument(
        "--num-transcripts",
        type=int,
        default=10,
        help="Number of transcripts to generate (default: 10).",
    )
    parser.add_argument(
        "--model",
        default="zai-org/glm-4.7",
        help="Model to use (default: openai/gpt-5.2).",
    )
    parser.add_argument(
        "--output",
        default="scripts/transcripts.csv",
        help="Output CSV path (default: scripts/transcripts.csv).",
    )
    parser.add_argument(
        "--start-date",
        default="2024-04-01",
        help="Start date for transcripts in YYYY-MM-DD format (default: 2024-04-01).",
    )
    parser.add_argument(
        "--date-spread",
        type=int,
        default=90,
        help="Number of days to spread transcripts across (default: 90).",
    )
    args = parser.parse_args()

    if not args.api_key:
        print("Error: provide --api-key or set NANOGPT_API_KEY env var.", file=sys.stderr)
        sys.exit(1)

    start_date = date.fromisoformat(args.start_date)
    if args.num_transcripts > 1:
        day_step = args.date_spread / (args.num_transcripts - 1)
    else:
        day_step = 0

    rows = []
    for i in range(args.num_transcripts):
        scenario = SCENARIOS[i % len(SCENARIOS)]
        tone = TONES[i % len(TONES)]
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        transcript_id = f"CALL_{suffix}"
        transcript_date = (start_date + timedelta(days=round(day_step * i))).isoformat()

        print(f"[{i + 1}/{args.num_transcripts}] Generating {transcript_id} ({transcript_date}): {scenario[:60]}...")

        try:
            lines = generate_transcript(args.api_key, scenario, args.model, args.base_url, tone)
        except Exception as e:
            print(f"  ERROR generating {transcript_id}: {e}", file=sys.stderr)
            continue

        if not lines:
            print(f"  WARNING: {transcript_id} returned no usable lines, skipping.")
            continue

        for idx, text in enumerate(lines):
            rows.append({
                "transcript_id": transcript_id,
                "transcript_index": idx,
                "text": text,
                "date": transcript_date,
            })

        print(f"  -> {len(lines)} sentences")
        time.sleep(0.5)  # gentle rate limiting

    if not rows:
        print("No transcripts generated.", file=sys.stderr)
        sys.exit(1)

    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        args.output,
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["transcript_id", "transcript_index", "text", "date"])
        writer.writeheader()
        writer.writerows(rows)

    n_transcripts = len(set(r["transcript_id"] for r in rows))
    print(f"\nDone! Wrote {len(rows)} rows ({n_transcripts} transcripts) to {output_path}")


if __name__ == "__main__":
    main()