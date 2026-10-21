"""DataForge Content Crew - Supervisor Agent
Phase 3/6: Agent Definitions & Topic Normalization
"""

import re
import json
from typing import Any, Dict
from services.gemini_service import generate_content


def normalize_topic(raw_prompt: str) -> str:
    """Strips command phrases, request words, and formatting instructions to extract the core subject."""
    if not raw_prompt:
        return "Autonomous Multi-Agent Architectures"

    text = raw_prompt.strip()

    # Strip conversational prefixes
    patterns = [
        r'^(?:please\s+)?(?:can you\s+|could you\s+|would you\s+)?(?:write|draft|create|generate|produce|compose|make)\s+(?:me\s+)?(?:an?\s+|the\s+)?(?:new\s+)?(?:blog(?:\s+post)?|article|post|guide|piece|summary|overview|whitepaper|analysis|playbook)?\s*(?:about|on|regarding|discussing|covering|for|explaining)?\s*',
        r'^(?:please\s+)?(?:explain|tell me about|deep dive into|breakdown|cover|give me an overview of)\s*',
        r'^(?:write|draft|create)\s+(?:about|on)\s*',
    ]
    for pat in patterns:
        cleaned = re.sub(pat, '', text, flags=re.IGNORECASE).strip()
        if cleaned and len(cleaned) >= 2 and cleaned != text:
            text = cleaned
            break

    # Strip trailing request modifiers
    trailing_patterns = [
        r'\s+(?:in\s+\d+\s+words|with\s+seo(?:\s+focus)?|for\s+(?:our\s+)?(?:blog|website|audience|enterprise)).*$',
        r'\s+please[\.\!\?]?$'
    ]
    for t_pat in trailing_patterns:
        text = re.sub(t_pat, '', text, flags=re.IGNORECASE).strip()

    # Clean up trailing punctuation
    text = re.sub(r'[\.\?\!\:\;]+$', '', text).strip()
    return text if text else raw_prompt.strip()


def run_supervisor(user_request: str, company_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Interprets user prompt, normalizes topic, and produces an editorial execution plan."""
    company_name = company_profile.get("company_name", "Your Organization")
    industry = company_profile.get("industry", "Technology")
    clean_topic = normalize_topic(user_request)

    system_prompt = (
        "You are the DataForge Content Crew Supervisor Agent. "
        "Your role is to analyze editorial requests, extract the core subject without command words "
        "(e.g., transform 'write blog on agentic AI' into topic 'Agentic AI'), "
        "and produce a structured 4-step execution plan with an engaging working title."
    )

    prompt = (
        f"Raw User Prompt: {user_request}\n"
        f"Normalized Topic Candidate: {clean_topic}\n"
        f"Company: {company_name} (Industry: {industry})\n\n"
        "Generate a concise JSON plan with the following keys:\n"
        "- topic: string (the pure subject, e.g. 'Agentic AI' - never include 'Write a blog on')\n"
        "- working_title: string (an engaging, reader-first editorial title for the article)\n"
        "- target_angle: string (unique strategic or architectural perspective)\n"
        "- steps: array of strings ['research', 'analysis', 'generation', 'review']"
    )

    llm_res = generate_content(prompt, system_instruction=system_prompt, json_mode=True)

    if llm_res["status"] == "success" and llm_res["text"]:
        try:
            parsed = json.loads(llm_res["text"])
            if "topic" in parsed:
                # Ensure returned topic doesn't accidentally have command words
                parsed["topic"] = normalize_topic(parsed["topic"])
                if not parsed.get("working_title"):
                    parsed["working_title"] = f"{parsed['topic'].title()}: Strategic Architecture and Implementation Playbook"
                return parsed
        except Exception:
            pass

    # High-quality deterministic fallback plan
    return {
        "topic": clean_topic,
        "working_title": f"{clean_topic.title()}: Strategic Framework and Operational Playbook",
        "target_angle": f"In-depth architectural analysis and actionable implementation for {industry} teams",
        "steps": ["research", "analysis", "generation", "review"],
        "is_fallback": True
    }
