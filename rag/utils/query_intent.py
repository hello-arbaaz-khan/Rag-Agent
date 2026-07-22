"""
Query-intent extraction for Advanced Search.

Turns a free-text search query (e.g. "give me the invoice file",
"file uploaded on 12/7/26", "files about cricket after 2030") into
structured intent:

    {
        "topic": "invoice" | None,
        "date_filter": {"type": "on"|"before"|"after"|"between"|None,
                         "date": "YYYY-MM-DD"|None,
                         "date_end": "YYYY-MM-DD"|None}
    }

This lets SearchService filter/rank on what the user actually meant
instead of doing a raw keyword/vector match on the whole sentence
(which is why "give me invoice file" used to return unrelated files,
and a query about a future date returned results anyway).
"""

import json
import logging
from datetime import date

from rag.utils.rag_engine import get_client

logger = logging.getLogger(__name__)

INTENT_MODEL = "llama-3.1-8b-instant"

INTENT_PROMPT_TEMPLATE = """You are the query-understanding module for a document search engine.
Today's date is {today}.

Read the user's search query and return STRICT JSON only (no prose, no markdown fences, no explanation) in exactly this shape:

{{
  "topic": "<the core subject/topic being searched for, with filler words like 'give me', 'find', 'show me', 'file', 'document' stripped out — or null if the query is only about a date/filter with no subject>",
  "date_filter": {{
    "type": "on" | "before" | "after" | "between" | null,
    "date": "YYYY-MM-DD" or null,
    "date_end": "YYYY-MM-DD" or null
  }}
}}

Rules:
- If the query references any date, absolute or relative ("uploaded on 12/7/26", "before last week", "after 2030", "yesterday's file"), resolve it to an ISO date using today's date as the reference point, and set date_filter.type accordingly ("on" for an exact day, "after"/"before" for one-sided ranges, "between" when two dates are given).
- Dates written as D/M/YY or D/M/YYYY are day/month/year, not month/day/year.
- If no date is referenced, date_filter must be {{"type": null, "date": null, "date_end": null}}.
- If the query is purely a date/filter request with no subject matter, set "topic" to null.
- Keep "topic" short — a few words naming the subject, e.g. "invoice", "cricket", "budget report".

Query: "{query}"

JSON:"""


def _strip_code_fences(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    return text.strip()


def parse_query_intent(query):
    """
    Ask the LLM to extract {topic, date_filter} from a search query.

    Never raises — on any failure (missing API key, network error,
    unparsable response) it falls back to treating the whole query as
    the topic with no date filter, so search degrades gracefully
    instead of breaking.
    """
    fallback = {
        "topic": query.strip() or None,
        "date_filter": {"type": None, "date": None, "date_end": None},
    }

    try:
        client = get_client()
        prompt = INTENT_PROMPT_TEMPLATE.format(today=date.today().isoformat(), query=query)
        response = client.chat.completions.create(
            model=INTENT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=200,
        )
        raw = _strip_code_fences(response.choices[0].message.content or "")
        data = json.loads(raw)

        topic = data.get("topic")
        topic = topic.strip() if isinstance(topic, str) else None
        topic = topic or None

        raw_filter = data.get("date_filter") or {}
        date_filter = {
            "type": raw_filter.get("type") or None,
            "date": raw_filter.get("date") or None,
            "date_end": raw_filter.get("date_end") or None,
        }

        return {"topic": topic, "date_filter": date_filter}

    except Exception as e:
        logger.warning("Query intent parsing failed, falling back to raw query: %s", e)
        return fallback