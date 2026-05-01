"""Generate the Monday MOPO scoreboard briefing using Claude.

Wire this into your daily/weekly refresh job: build the scoreboard data dict
as today, call `add_briefing(data)` before writing the JSON file, done.

Auth: set ANTHROPIC_API_KEY in the environment.
Install: pip install anthropic

Cost: ~10K input tokens + ~2K output tokens on Sonnet 4.6 = roughly $0.06 per run.
Cache note: prompt-caching markers are included as requested but provide no real
benefit on a weekly cadence (cache TTL is 1 hour max). If you increase frequency
to daily or sub-daily the cache will start paying off; on Mondays-only it's a
small write premium with no reads. Harmless either way.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic


MODEL = "claude-sonnet-4-6"


BRIEFING_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "headline": {"type": "string"},
        "worst_regions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "region": {"type": "string"},
                    "drr_usd": {"type": "number"},
                    "prior_drr_usd": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "reason": {"type": "string"},
                },
                "required": ["region", "drr_usd", "prior_drr_usd", "reason"],
            },
        },
        "deteriorating": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "level": {"type": "string", "enum": ["region", "hub"]},
                    "from": {"type": "number"},
                    "to": {"type": "number"},
                    "note": {"type": "string"},
                },
                "required": ["name", "level", "from", "to", "note"],
            },
        },
        "focus": {"type": "string"},
        "region_questions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "region": {"type": "string"},
                    "wow_delta": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "questions": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["region", "wow_delta", "questions"],
            },
        },
    },
    "required": ["headline", "worst_regions", "deteriorating", "focus", "region_questions"],
}


SYSTEM_PROMPT = """You are a senior operations analyst at MOPO, writing the Monday morning briefing for the regional manager who oversees Nigeria MOPO50 hubs.

CONTEXT
- The wildly important goal (WIG) is to grow Nigeria MOPO50 DRR from $0.13 to $0.18 per battery per day by 1 September 2026.
- DRR = Daily Rental Revenue per available battery, USD-converted (rental income / batteries available / official NGN-USD rate).
- The user oversees a subset of regions and uses this briefing to pick interventions and meet team leads on Monday morning.
- Your job: surface where to focus and what to ask each regional team lead.

INPUT (in the user message as JSON)
- regions[]: each region's current drr_usd, hub count, and prior_drr_usd (last week)
- lead_relative / lead_earnings: agent-level lead measures (below 35% of hub-best DRR; below regional P25 earnings floor)
- flagged_agents[]: agents flagged on both lead measures, with hub_drr, hub_best_drr, agent_drr, rel_perf %, weekly NGN earnings, days_in_role
- new_agents.by_region[]: 30-day intake performance per region (above_target / progressing / below_baseline counts)
- window_start, window_end: data window for this report

OUTPUT (matches the enforced schema)
- headline: ONE sentence framing the week. Lead with the dominant signal.
- worst_regions: 2-4 regions, worst first. `reason` is 1-2 sentences citing specific data points (flagged counts, hub-best gaps, intake quality). Never invent numbers.
- deteriorating: regions or hubs that got worse vs prior week, with from/to numbers. Skip if nothing meaningful deteriorated.
- focus: 2-4 sentences. Where Monday's energy should go. Be willing to deprioritise things explicitly. Use HTML <strong> tags for emphasis (renders inline in the dashboard).
- region_questions: ONE entry per region present in the data. 3-5 evidence-based, specific questions per region — citing the exact figure or pattern that prompted them. Skip generic management-101 questions ("what's blocking the team").
  - wow_delta: short string like "↓ 18% WoW", "↑ 6% WoW", "flat", computed from prior_drr_usd → drr_usd.

TONE
- Direct, opinionated, operationally literate. Skip definitions; the reader knows DRR.
- Honest about what's working — if a region is healthy, ask the question that surfaces transferable lessons rather than padding negativity.
- Never invent numbers, names, or hubs not present in the input data."""


def add_briefing(data: dict, *, model: str = MODEL, client: anthropic.Anthropic | None = None) -> dict:
    """Generate the Monday briefing for `data` and attach it as `data['briefing']`.

    Mutates `data` in place and returns it. Strips any prior `briefing` field
    before calling so re-runs are deterministic.
    """
    client = client or anthropic.Anthropic()
    payload = {k: v for k, v in data.items() if k != "briefing"}

    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        output_config={"format": {"type": "json_schema", "schema": BRIEFING_SCHEMA}},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Data window {payload.get('window_start')} to {payload.get('window_end')}.\n"
                    f"Generate the Monday briefing for this scoreboard data:\n\n"
                    f"{json.dumps(payload, indent=2)}"
                ),
            }
        ],
    )

    if response.stop_reason == "refusal":
        raise RuntimeError("Claude refused the briefing request")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Briefing truncated at max_tokens — bump max_tokens")

    text = next(b.text for b in response.content if b.type == "text")
    briefing = json.loads(text)
    briefing["model"] = f"Claude {model.replace('claude-', '').replace('-', ' ').title()}"
    briefing["generated_at"] = datetime.now(timezone.utc).isoformat()

    data["briefing"] = briefing

    u = response.usage
    print(
        f"[briefing] tokens: input={u.input_tokens} output={u.output_tokens} "
        f"cache_read={u.cache_read_input_tokens} cache_write={u.cache_creation_input_tokens}"
    )
    return data


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "mopo_scoreboard_data.json")
    data = json.loads(path.read_text())
    add_briefing(data)
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"[briefing] wrote {path}")


if __name__ == "__main__":
    main()
