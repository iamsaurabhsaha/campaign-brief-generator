"""
LLM Provider Abstraction Layer
================================
Unified interface for multiple LLM providers: Anthropic, OpenAI, Azure OpenAI,
Google Gemini, AWS Bedrock, and Ollama (local).

Configuration is driven entirely by environment variables:
    LLM_PROVIDER        — anthropic | openai | azure | gemini | bedrock | ollama
    LLM_MODEL           — model name for the chosen provider
    LLM_BASE_URL        — optional custom base URL (for OpenAI-compatible APIs)
    ANTHROPIC_API_KEY    — Anthropic API key
    OPENAI_API_KEY       — OpenAI / Azure OpenAI API key
    AZURE_OPENAI_ENDPOINT — Azure OpenAI endpoint URL
    AZURE_OPENAI_API_VERSION — Azure API version (default: 2024-10-21)
    GOOGLE_API_KEY       — Google Gemini API key
    AWS_REGION           — AWS region for Bedrock (default: us-east-1)
    OLLAMA_BASE_URL      — Ollama server URL (default: http://localhost:11434)
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default models per provider
# ---------------------------------------------------------------------------

DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "azure": "gpt-4o",
    "gemini": "gemini-2.5-flash",
    "bedrock": "anthropic.claude-sonnet-4-20250514-v1:0",
    "ollama": "llama3.1",
}


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------


def _call_anthropic(
    system: str, user_prompt: str, max_tokens: int, model: str
) -> str:
    """Call Anthropic Claude API."""
    from anthropic import Anthropic

    client = Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )
    # Handle potential thinking blocks — find the text block
    for block in response.content:
        if hasattr(block, "text"):
            return block.text
    # Fallback to first block
    return response.content[0].text


def _call_openai(
    system: str, user_prompt: str, max_tokens: int, model: str
) -> str:
    """Call OpenAI API (or any OpenAI-compatible endpoint via LLM_BASE_URL)."""
    from openai import OpenAI

    base_url = os.environ.get("LLM_BASE_URL")
    client = OpenAI(**({"base_url": base_url} if base_url else {}))
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


def _call_azure(
    system: str, user_prompt: str, max_tokens: int, model: str
) -> str:
    """Call Azure OpenAI API."""
    from openai import AzureOpenAI

    client = AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ.get("OPENAI_API_KEY"),
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


def _call_gemini(
    system: str, user_prompt: str, max_tokens: int, model: str
) -> str:
    """Call Google Gemini API."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text


def _call_bedrock(
    system: str, user_prompt: str, max_tokens: int, model: str
) -> str:
    """Call AWS Bedrock (supports Anthropic Claude models on Bedrock)."""
    import boto3
    import json

    region = os.environ.get("AWS_REGION", "us-east-1")
    client = boto3.client("bedrock-runtime", region_name=region)

    # Bedrock Anthropic models use the messages API format
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user_prompt}],
    })

    response = client.invoke_model(
        modelId=model,
        contentType="application/json",
        accept="application/json",
        body=body,
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def _call_ollama(
    system: str, user_prompt: str, max_tokens: int, model: str
) -> str:
    """Call local Ollama server via its OpenAI-compatible API."""
    from openai import OpenAI

    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    client = OpenAI(base_url=f"{base_url}/v1", api_key="ollama")
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Provider dispatch
# ---------------------------------------------------------------------------

_PROVIDERS = {
    "anthropic": _call_anthropic,
    "openai": _call_openai,
    "azure": _call_azure,
    "gemini": _call_gemini,
    "bedrock": _call_bedrock,
    "ollama": _call_ollama,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_provider() -> str:
    """Return the configured LLM provider name."""
    return os.environ.get("LLM_PROVIDER", "anthropic").lower().strip()


def get_model() -> str:
    """Return the configured model name (or default for the provider)."""
    provider = get_provider()
    return os.environ.get("LLM_MODEL", DEFAULT_MODELS.get(provider, ""))


def is_configured() -> bool:
    """Check whether the current provider has the required credentials.

    Returns True for Ollama (no key needed) and demo mode detection.
    """
    provider = get_provider()

    if provider == "ollama":
        return True
    if provider == "anthropic":
        return bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
    if provider in ("openai", "azure"):
        return bool(os.environ.get("OPENAI_API_KEY", "").strip())
    if provider == "gemini":
        return bool(os.environ.get("GOOGLE_API_KEY", "").strip())
    if provider == "bedrock":
        # Bedrock uses AWS credentials (env vars or IAM role)
        return True

    return False


def generate(
    system: str,
    user_prompt: str,
    max_tokens: int = 4096,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """Send a prompt to the configured LLM and return the raw text response.

    Args:
        system: System prompt / instructions.
        user_prompt: User message.
        max_tokens: Maximum tokens in the response.
        provider: Override the env-configured provider.
        model: Override the env-configured model.

    Returns:
        Raw text response from the LLM.

    Raises:
        ValueError: If the provider is not supported.
        Various SDK exceptions depending on the provider.
    """
    prov = (provider or get_provider()).lower().strip()
    mdl = model or get_model()

    if prov not in _PROVIDERS:
        raise ValueError(
            f"Unsupported LLM provider: '{prov}'. "
            f"Choose from: {', '.join(_PROVIDERS.keys())}"
        )

    logger.info("LLM call: provider=%s, model=%s, max_tokens=%d", prov, mdl, max_tokens)
    return _PROVIDERS[prov](system, user_prompt, max_tokens, mdl)


def provider_display_name() -> str:
    """Return a human-readable label for the active provider + model."""
    provider = get_provider()
    model = get_model()
    labels = {
        "anthropic": "Anthropic",
        "openai": "OpenAI",
        "azure": "Azure OpenAI",
        "gemini": "Google Gemini",
        "bedrock": "AWS Bedrock",
        "ollama": "Ollama (Local)",
    }
    return f"{labels.get(provider, provider)} — {model}"
