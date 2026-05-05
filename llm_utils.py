"""
LLM + data profiling utilities for the Chat with Your CSV app.

Two responsibilities:
  1) Turn a pandas DataFrame into a compact text summary the LLM can reason over
     (build_data_context).
  2) Stream a user's question through OpenAI and yield reply chunks plus token
     usage (ask_llm_stream).

Kept in a separate module from app.py so the Streamlit UI stays readable and so
the data / LLM layer can be unit-tested or swapped out independently.
"""

from __future__ import annotations

from typing import Iterator, Optional

import pandas as pd
import streamlit as st
from openai import OpenAI


# ---------------------------------------------------------------------------
# Available models and pricing
# ---------------------------------------------------------------------------
#
# Pricing is in USD per 1,000,000 tokens. Sourced from OpenAI's public pricing
# page. Update these numbers if OpenAI changes pricing or you add new models.

MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.150, "output": 0.600},
    "gpt-4o":      {"input": 2.500, "output": 10.000},
}

AVAILABLE_MODELS = list(MODEL_PRICING.keys())

# LLM call settings
MAX_RESPONSE_TOKENS = 700
TEMPERATURE = 0.2
HISTORY_TURNS_TO_KEEP = 6


SYSTEM_PROMPT_TEMPLATE = """You are a data analyst assistant. The user has uploaded a CSV file \
and will ask you questions about it in plain English.

Answer their questions using ONLY the data summary below. Be precise, concise, and data-driven. \
If the summary does not contain enough information to answer a question (for example, the user \
asks for a specific value you cannot compute from the summary), say so clearly and suggest what \
the user could check in the raw data.

When relevant, reference specific column names and values from the summary. Keep answers to \
2 to 4 short paragraphs unless the user explicitly asks for more detail.

=== DATA SUMMARY ===
{data_context}
===================="""


# ---------------------------------------------------------------------------
# OpenAI client
# ---------------------------------------------------------------------------

def get_openai_client() -> OpenAI:
    """
    Build an OpenAI client using the API key from Streamlit secrets.

    Works identically in two environments:
      - Local dev: reads from .streamlit/secrets.toml
      - Streamlit Community Cloud: reads from the app's Secrets setting

    If the key is missing we stop the app with a friendly error instead of
    crashing with a stack trace.
    """
    # Streamlit raises if secrets.toml does not exist at all (a separate
    # case from "the file is there but lacks our key"), so wrap the read
    # in try/except to keep the user-facing error friendly either way.
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        api_key = None

    if not api_key:
        st.error(
            "OpenAI API key not found.\n\n"
            "**Local:** create `.streamlit/secrets.toml` with `OPENAI_API_KEY = \"sk-...\"`\n\n"
            "**Cloud:** add `OPENAI_API_KEY` in your Streamlit Community Cloud "
            "app Settings → Secrets."
        )
        st.stop()

    return OpenAI(api_key=api_key)


# ---------------------------------------------------------------------------
# Data profiling: turn a DataFrame into LLM-ready context
# ---------------------------------------------------------------------------

def build_data_context(df: pd.DataFrame) -> str:
    """
    Produce a compact text profile of a DataFrame for the LLM.

    The profile covers:
      - Shape (rows, columns)
      - Column names and dtypes
      - Summary statistics for numeric columns (df.describe)
      - Top value counts for a few categorical columns
      - First 5 sample rows
      - Missing-value counts per column

    Total length usually lands around 1,000 to 3,000 tokens, which fits
    comfortably in any modern OpenAI model's context window.
    """
    parts: list[str] = []

    # 1. Shape
    parts.append(f"Dataset shape: {df.shape[0]:,} rows x {df.shape[1]} columns")

    # 2. Columns and dtypes
    parts.append("\nColumns and data types:")
    for col, dtype in df.dtypes.items():
        parts.append(f"  - {col}: {dtype}")

    # 3. Numeric summary stats
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        parts.append("\nNumeric column statistics (from df.describe):")
        desc = df[numeric_cols].describe().round(2).to_string()
        parts.append(desc)

    # 4. Categorical / text columns: show top values
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if cat_cols:
        parts.append("\nCategorical / text columns (top 5 values each):")
        for col in cat_cols[:5]:           # Limit to 5 columns to keep context bounded
            counts = df[col].value_counts(dropna=False).head(5)
            parts.append(f"\n  {col}:")
            for val, count in counts.items():
                parts.append(f"    {val}: {count:,}")

    # 5. Sample rows
    parts.append("\nFirst 5 rows (as a sample of what the raw data looks like):")
    parts.append(df.head(5).to_string(index=False))

    # 6. Missing values summary
    null_counts = df.isna().sum()
    has_nulls = null_counts[null_counts > 0]
    if not has_nulls.empty:
        parts.append("\nColumns with missing values (count):")
        for col, n in has_nulls.items():
            parts.append(f"  - {col}: {n:,}")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# The actual LLM call (streaming)
# ---------------------------------------------------------------------------

def ask_llm_stream(
    user_message: str,
    data_context: str,
    history: list[dict],
    model: str = "gpt-4o-mini",
    usage_tracker: Optional[dict] = None,
) -> Iterator[str]:
    """
    Stream the LLM's reply chunk-by-chunk for use with `st.write_stream`.

    Parameters
    ----------
    user_message : str
        The latest message from the user.
    data_context : str
        The data profile produced by build_data_context. Injected into the
        system prompt so the model grounds its answers.
    history : list of dict
        Prior chat history as [{"role": ..., "content": ...}]. Truncated to
        the last few turns to keep the request small.
    model : str
        The OpenAI model to use, e.g. "gpt-4o-mini" or "gpt-4o".
    usage_tracker : dict, optional
        If provided, this dict is populated after the stream finishes with
        keys "input_tokens" and "output_tokens" so the caller can render
        token / cost metrics.

    Yields
    ------
    str
        Each content chunk as it arrives from the API.
    """
    client = get_openai_client()

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(data_context=data_context)

    messages: list[dict] = [{"role": "system", "content": system_prompt}]

    # Keep only the tail of the conversation to bound cost
    for msg in history[-HISTORY_TURNS_TO_KEEP:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_RESPONSE_TOKENS,
            stream=True,                              # response becomes an iterator of chunks
            stream_options={"include_usage": True},   # final chunk carries token totals
        )

        for chunk in stream:
            # Content chunk: delta carries a slice of the assistant's reply.
            # The defensive guard skips the final usage-only chunk, whose
            # `choices` list is empty.
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

            # Usage chunk: only the FINAL chunk has chunk.usage populated
            # (earlier ones are None), so guard with getattr to be safe.
            if getattr(chunk, "usage", None):
                if usage_tracker is not None:
                    usage_tracker["input_tokens"] = chunk.usage.prompt_tokens
                    usage_tracker["output_tokens"] = chunk.usage.completion_tokens

    except Exception as e:
        # Surface the error in the chat instead of crashing the app
        yield f"\n\nError calling OpenAI: {e}"
