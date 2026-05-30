"""Phase 3 — Response generator.

Orchestrates the full query flow:
1. PII detection → refuse if found (NO URL)
2. Query classification → refuse if advisory/out-of-scope (NO URL)
3. Retrieval → get context
4. Generate answer using Groq LLM (with template fallback) OR refuse if not found (NO URL)
5. Validate response
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional
import logging

from app.guardrails.classifier import classify_query, QueryCategory
from app.guardrails.pii_filter import detect_pii, contains_pii
from app.guardrails.refusal import create_refusal_response, get_refusal_reason
from app.guardrails.validator import validate_response
from app.rag.retriever import retrieve
from app.rag.context_assembler import assemble_context, get_citation_url

logger = logging.getLogger(__name__)

_EXIT_LOAD_SENTENCE = re.compile(
    r"exit load[^.\n]*?(?:redeemed|within)[^.\n]*",
    re.IGNORECASE,
)
_EXIT_LOAD_NIL = re.compile(
    r"exit load\s*(?:\([^)]*\))?\s*:?\s*\n\s*(nil|none|0%|not applicable)",
    re.IGNORECASE,
)


def _extract_exit_load_answer(context: str) -> Optional[str]:
    """Extract one exit-load sentence from retrieved context."""
    if _EXIT_LOAD_NIL.search(context):
        return "Exit load is Nil."

    for line in context.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith(("[Scheme:", "Query:", "--- Chunk")):
            continue
        lower = stripped.lower()
        if "exit load" not in lower:
            continue
        if "redeemed" in lower or "within" in lower:
            for sentence in re.split(r"(?<=[.!?])\s+", stripped):
                sentence = sentence.strip()
                s_lower = sentence.lower()
                if "exit load" in s_lower and ("redeemed" in s_lower or "within" in s_lower):
                    if not sentence.endswith("."):
                        sentence += "."
                    return sentence
            if len(stripped) < 120:
                if not stripped.endswith("."):
                    stripped += "."
                return stripped

    match = _EXIT_LOAD_SENTENCE.search(context)
    if match:
        answer = match.group(0).strip()
        if not answer.endswith("."):
            answer += "."
        return answer

    return None


def get_footer_date() -> str:
    """Get footer date from corpus metadata or current date."""
    # TODO: Read from corpus/last_updated.json
    # For now, use current date
    return f"Last updated from sources: {datetime.now().strftime('%Y-%m-%d')}"


def generate_answer(
    query: str,
    context: str,
    citation_url: str,
    footer_date: str,
) -> dict:
    """Generate a factual answer response using Groq LLM.
    
    Uses Groq LLM for natural language generation with template-based fallback.
    
    Args:
        query: User query
        context: Retrieved context from corpus
        citation_url: Source URL for citation
        footer_date: Footer date string
        
    Returns:
        Answer response dict
    """
    # Try Groq LLM first
    try:
        from app.rag.llm import generate_answer_with_llm
        
        logger.info(f"Generating answer with Groq LLM for query: {query}")
        response = generate_answer_with_llm(
            query=query,
            context=context,
            citation_url=citation_url,
            footer_date=footer_date,
        )
        
        # Validate LLM response
        is_valid, errors = validate_response(response)
        if is_valid:
            logger.info("LLM response validated successfully")
            return response
        else:
            logger.warning(f"LLM response validation failed: {errors}, using template fallback")
            
    except (ImportError, ValueError) as e:
        # Groq not available or not configured - use template fallback
        logger.info(f"Groq LLM not available ({e}), using template-based generation")
    except Exception as e:
        # Any other error - use template fallback
        logger.warning(f"LLM generation failed ({e}), using template fallback")
    
    # Fallback to template-based generation (Phase 3 original)
    return _generate_template_answer(query, context, citation_url, footer_date)


def _generate_template_answer(
    query: str,
    context: str,
    citation_url: str,
    footer_date: str,
) -> dict:
    """Template-based answer generation (fallback when LLM unavailable).
    
    Args:
        query: User query
        context: Retrieved context from corpus
        citation_url: Source URL for citation
        footer_date: Footer date string
        
    Returns:
        Answer response dict
    """
    query_lower = query.lower()
    lines = context.split('\n')
    
    # Filter out header/metadata lines to avoid false matches
    content_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip context assembler headers
        if stripped.startswith('[Scheme:') or stripped.startswith('Query:') or stripped.startswith('--- Chunk'):
            continue
        content_lines.append(line)
    
    # Strategy: Find the specific fact based on query keywords
    answer_text = None
    
    # Expense ratio query
    if 'expense' in query_lower or 'ratio' in query_lower:
        for line in lines:
            match = re.search(
                r"expense\s+ratio[^\d]*(\d+(?:\.\d+)?%)",
                line,
                re.IGNORECASE,
            )
            if match:
                answer_text = f"The expense ratio is {match.group(1)}."
                break
        if not answer_text:
            for i, line in enumerate(lines):
                if 'expense ratio' in line.lower():
                    if i + 1 < len(lines):
                        value = lines[i + 1].strip()
                        if value and any(c.isdigit() for c in value):
                            answer_text = f"The expense ratio is {value}."
                            break
    
    # Exit load query
    elif 'exit' in query_lower or 'load' in query_lower:
        answer_text = _extract_exit_load_answer(context)
    
    # SIP minimum query
    elif 'sip' in query_lower or 'minimum' in query_lower:
        for i, line in enumerate(lines):
            if 'min. for sip' in line.lower() or 'minimum sip' in line.lower():
                # Next line should have the value
                if i + 1 < len(lines):
                    value = lines[i + 1].strip()
                    if value and ('₹' in value or 'rs' in value.lower() or any(c.isdigit() for c in value)):
                        answer_text = f"The minimum SIP amount is {value}."
                        break
    
    # Benchmark query
    elif 'benchmark' in query_lower:
        for i, line in enumerate(content_lines):
            if 'fund benchmark' in line.lower() or line.strip().lower() == 'benchmark':
                # Next line should have the benchmark name
                if i + 1 < len(content_lines):
                    value = content_lines[i + 1].strip()
                    if value and len(value) > 5 and any(c.isalpha() for c in value):
                        answer_text = f"The benchmark is {value}."
                        break
            elif 'benchmark' in line.lower() and ':' in line:
                # Extract benchmark name from "Benchmark: XYZ" format
                parts = line.split(':', 1)
                if len(parts) == 2 and len(parts[1].strip()) > 5:
                    answer_text = f"The benchmark is {parts[1].strip()}."
                    break
    
    # Fund manager query
    elif 'manager' in query_lower or 'fund manager' in query_lower:
        for line in lines:
            if any(name in line for name in ['Mr.', 'Ms.', 'Mrs.']) and len(line) < 100:
                answer_text = line.strip()
                if not answer_text.endswith('.'):
                    answer_text += '.'
                break
    
    # NAV (Net Asset Value) query
    elif 'nav' in query_lower:
        for i, line in enumerate(lines):
            if 'nav:' in line.lower() or line.strip().startswith('NAV:'):
                # NAV line has format: "NAV: 25 May '26"
                nav_date = line.strip()
                # Next line should have the value
                if i + 1 < len(lines):
                    nav_value = lines[i + 1].strip()
                    if nav_value and ('₹' in nav_value or any(c.isdigit() for c in nav_value)):
                        answer_text = f"The {nav_value} (as of {nav_date.replace('NAV:', '').strip()})."
                        break
    
    # AUM (Assets Under Management) / Fund Size query
    elif 'aum' in query_lower or 'fund size' in query_lower or 'assets' in query_lower:
        for i, line in enumerate(lines):
            if 'fund size' in line.lower() or 'aum' in line.lower():
                # Next line should have the value
                if i + 1 < len(lines):
                    value = lines[i + 1].strip()
                    if value and ('₹' in value or 'cr' in value.lower() or any(c.isdigit() for c in value)):
                        answer_text = f"The fund size (AUM) is {value}."
                        break
    
    # Riskometer / Risk classification query
    elif 'risk' in query_lower or 'riskometer' in query_lower:
        for line in content_lines:
            # Look for "rated Very High risk" or "Risk classification" patterns
            line_lower = line.lower()
            if ('rated' in line_lower and 'risk' in line_lower) or \
               ('risk classification' in line_lower) or \
               ('riskometer' in line_lower):
                # Extract just the risk-related sentence
                full_text = line.strip()
                # Find the sentence that contains the risk info
                sentences = full_text.split('.')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence and 'risk' in sentence.lower():
                        answer_text = sentence + '.'
                        break
                if not answer_text:
                    # Fallback to first sentence
                    first_sentence = sentences[0].strip()
                    if first_sentence:
                        answer_text = first_sentence + '.'
                break
        # Fallback: look for risk level keywords
        if not answer_text:
            for line in content_lines:
                line_lower = line.lower()
                if ('very high' in line_lower or 
                    (line_lower.count('high') > 0 and 'risk' in line_lower) or 
                    'moderate' in line_lower or 
                    'low' in line_lower) and 'risk' in line_lower:
                    answer_text = line.strip()
                    if not answer_text.endswith('.'):
                        answer_text += '.'
                    break
    
    # ELSS lock-in period query
    elif 'elss' in query_lower or 'lock-in' in query_lower or 'lock in' in query_lower:
        for line in content_lines:
            line_lower = line.lower()
            if ('lock-in' in line_lower or 'lock in' in line_lower) and ('year' in line_lower or 'yr' in line_lower):
                answer_text = line.strip()
                if not answer_text.endswith('.'):
                    answer_text += '.'
                break
        # Fallback: search for ELSS-specific text
        if not answer_text:
            for i, line in enumerate(content_lines):
                if 'elss' in line.lower() and ('tax' in line.lower() or 'saver' in line.lower()):
                    # Check next few lines for lock-in info
                    for j in range(i, min(i+3, len(content_lines))):
                        if 'lock' in content_lines[j].lower() and ('year' in content_lines[j].lower() or 'yr' in content_lines[j].lower()):
                            answer_text = content_lines[j].strip()
                            if not answer_text.endswith('.'):
                                answer_text += '.'
                            break
                    if answer_text:
                        break
    
    # Fallback: Find any relevant short fact
    if not answer_text:
        for line in content_lines:
            line = line.strip()
            # Look for informative lines (not too short, not too long)
            if 15 < len(line) < 150 and not line.startswith('[') and not line.startswith('---'):
                # Skip lines that are just numbers or symbols
                if any(c.isalpha() for c in line):
                    answer_text = line
                    if not answer_text.endswith('.'):
                        answer_text += '.'
                    break
    
    # Final fallback
    if not answer_text:
        answer_text = "Information not found in the corpus."
    
    return {
        "type": "answer",
        "text": answer_text,
        "citation_url": citation_url,
        "footer": footer_date,
        "refused": False,
    }


def process_query(query: str, top_k: int = 3) -> dict:
    """Process a user query through the full guardrails pipeline.
    
    Args:
        query: User query string
        top_k: Number of chunks to retrieve
        
    Returns:
        Response dict (answer or refusal)
    """
    footer_date = get_footer_date()
    
    # Step 1: PII Detection
    if contains_pii(query):
        return create_refusal_response(
            reason="pii_detected",
            footer_date=footer_date,
        )
    
    # Step 2: Query Classification
    category, reason = classify_query(query)
    
    if category == QueryCategory.ADVISORY:
        return create_refusal_response(
            reason="advisory_query",
            footer_date=footer_date,
        )
    
    if category == QueryCategory.OUT_OF_SCOPE:
        return create_refusal_response(
            reason="out_of_scope",
            footer_date=footer_date,
        )
    
    # Step 3: Retrieval (factual query)
    response = retrieve(query, top_k=top_k)
    
    # Check if we got results
    if not response.results:
        return create_refusal_response(
            reason="answer_not_found",
            footer_date=footer_date,
        )
    
    # Step 4: Build context
    context = assemble_context(response)
    citation_url = get_citation_url(response)
    
    if not citation_url:
        return create_refusal_response(
            reason="answer_not_found",
            footer_date=footer_date,
        )
    
    # Step 5: Generate answer
    answer = generate_answer(
        query=query,
        context=context,
        citation_url=citation_url,
        footer_date=footer_date,
    )
    
    # Step 6: Validate (retry template if LLM answer fails validation)
    is_valid, errors = validate_response(answer)
    if not is_valid:
        logger.warning("Answer validation failed (%s), retrying with template", errors)
        template_answer = _generate_template_answer(
            query=query,
            context=context,
            citation_url=citation_url,
            footer_date=footer_date,
        )
        is_valid, errors = validate_response(template_answer)
        if is_valid:
            return template_answer
        return create_refusal_response(
            reason="answer_not_found",
            footer_date=footer_date,
        )
    
    return answer
