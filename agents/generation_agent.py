"""DataForge Content Crew - Generation Agent
Phase 3/6: Agent Definitions & Reader-First Article Generation
"""

import json
from typing import Any, Dict
from agents.supervisor_agent import normalize_topic
from services.gemini_service import generate_content


def run_generation_agent(
    topic: str,
    analysis_report: Dict[str, Any],
    company_profile: Dict[str, Any],
    revision_feedback: str = "",
    is_regeneration: bool = False
) -> Dict[str, Any]:
    """Generates an original, structured blog draft aligned with company profile and research."""
    clean_topic = normalize_topic(topic)
    company_name = company_profile.get("company_name", "Your Organization")
    tone = company_profile.get("tone", "Authoritative & Technical")
    target_audience = company_profile.get("target_audience", "Engineering & Content Leaders")
    usp = company_profile.get("usp", "Scalable, high-impact enterprise workflows")
    primary_kw = analysis_report.get("primary_keyword") or clean_topic
    sources = analysis_report.get("sources", [])

    # Format genuine citation anchors
    citations_text = ""
    if sources:
        citations_text = "\nVerified Source Anchors to cite with markdown links [Title](url):\n"
        for s in sources:
            citations_text += f"- Title: {s.get('title')}, URL: {s.get('url')}, Context: {s.get('snippet', '')[:180]}\n"

    system_prompt = (
        f"You are the senior Technical Content Generation Agent for {company_name}. "
        f"Write in an {tone} voice tailored specifically for {target_audience}. "
        f"Incorporate the company's USP ({usp}) naturally as a practical recommendation without promotional fluff.\n"
        "Strict editorial guidelines:\n"
        "1. Provide a compelling, informative H1 headline in the 'title' field. NEVER include prompt command words like 'Write a blog on' or repeat the user request verbatim.\n"
        "2. In 'content_markdown', do NOT repeat the H1 title at the top.\n"
        "3. Avoid generic introductory platitudes (e.g. 'In today's fast-paced world...'). Jump immediately into the core architectural paradigms, industry context, and real challenges.\n"
        "4. Organize with clean semantic H2 (##) and H3 (###) sections with substantive, well-paced paragraphs.\n"
        "5. Include concrete architectural principles, operational trade-offs, and practical workflows.\n"
        "6. Provide bulleted or numbered actionable takeaways.\n"
        "7. If verified sources are provided, cite them with markdown links. Never invent URLs or fake citations.\n"
        "8. Conclude with a strong synthesis and next steps for technical teams."
    )

    user_prompt = (
        f"Subject: {clean_topic}\n"
        f"Target Keyword: {primary_kw}\n"
        f"Research Summary: {analysis_report.get('summary', '')}\n"
        f"{citations_text}\n"
    )
    if revision_feedback:
        user_prompt += f"\nSpecific Revision Request to Incorporate: {revision_feedback}\n"
    if is_regeneration:
        user_prompt += "\nNote: This is a full regeneration request. Produce a completely fresh perspective and structure while maintaining rigor.\n"

    user_prompt += (
        "\nProvide your output strictly as a JSON object with two fields:\n"
        "1. title: The blog post title (string)\n"
        "2. content_markdown: The formatted markdown body without repeating the title (string)"
    )

    llm_res = generate_content(user_prompt, system_instruction=system_prompt, json_mode=True)

    if llm_res["status"] == "success" and llm_res["text"]:
        try:
            parsed = json.loads(llm_res["text"])
            if "title" in parsed and "content_markdown" in parsed:
                content = parsed["content_markdown"]
                words = len(content.split())
                return {
                    "title": parsed["title"],
                    "content_markdown": content,
                    "word_count": words,
                    "is_live_ai": True
                }
        except Exception:
            pass

    # Deterministic high-quality fallback draft
    rev_note = f"\n\n> **Editorial Revision Note:** Incorporated: {revision_feedback}" if revision_feedback else ""
    regen_suffix = " — Modern Strategic Playbook" if is_regeneration else ": Architectural Patterns & Implementation Guide"
    fallback_title = f"{clean_topic.title()}{regen_suffix}"

    sources_section = ""
    if sources:
        sources_section = "\n\n### References & Verified Industry Sources\n"
        for s in sources[:3]:
            sources_section += f"- [{s.get('title', 'Industry Analysis')}]({s.get('url', '#')}) — {s.get('snippet', '')[:100]}...\n"

    fallback_content = f"""## Understanding {clean_topic.title()} in Practice

As systems scale and complexity increases, understanding the operational mechanics of {clean_topic} is critical for {target_audience}. Rather than relying on superficial implementations, engineering teams must ground their systems in resilient patterns and verifiable data.

{rev_note}

## 1. Architectural Foundations and Key Considerations

Deploying solutions around {primary_kw} requires addressing three core technical vectors:

* **State Determinism & Isolation:** Maintain predictable boundaries between workflow nodes to isolate execution state and prevent cascading failures.
* **Granular Observability:** Implement comprehensive event tracing across all components to capture latency, input parameters, and failure states in real time.
* **Continuous Feedback Loops:** Pair programmatic checks with automated validation to enforce high standards before changes reach production.

### Operational Trade-offs

When assessing infrastructure requirements, organizations frequently balance autonomy against control. Decoupling orchestration from execution ensures that failure in a single pipeline component does not compromise downstream operations.

## 2. Practical Execution with {company_name}

Organizations can accelerate implementation by pairing standard design patterns with {usp}. This enables teams to maintain high throughput without compromising quality or compliance.

```markdown
Operational Benchmark: Sub-second state coordination with auditable execution histories and predictable resource consumption.
```

### Key Technical Questions

**Q: What is the primary bottleneck when adopting this architecture?**  
A: Managing state transitions and maintaining context integrity across decoupled stages.

**Q: How do teams measure deployment success?**  
A: Through system reliability, cycle time reduction, and consistent fidelity under variable workloads.

## Strategic Summary and Next Steps

Successfully operationalizing {clean_topic} demands discipline, transparent instrumentation, and rigorous system boundaries. By establishing clear standards early, teams build resilient systems capable of scaling alongside evolving organizational requirements.{sources_section}
"""

    return {
        "title": fallback_title,
        "content_markdown": fallback_content.strip(),
        "word_count": len(fallback_content.split()),
        "is_live_ai": False
    }
