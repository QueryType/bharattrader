"""
Report Generator Module

This module handles the generation of equity research reports using LLMs.
"""

import os
import re
import logging
import json
from pathlib import Path
import datetime
from typing import List, Dict, Any, Optional, Tuple

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load variables from .env
    ENV_LOADED = True
except ImportError:
    ENV_LOADED = False
    logging.warning("dotenv not found, environment variables must be set manually")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get model IDs and config from environment variables
OPENAI_TEXT_MODEL = os.environ.get("OPENAI_TEXT_MODEL", "gpt-4-turbo")
OPENAI_VISION_MODEL = os.environ.get("OPENAI_VISION_MODEL", "gpt-4-vision-preview")
# Flag to enable/disable LLM prompt logging (default: enabled)
ENABLE_LOGGING = os.environ.get("ENABLE_LLM_LOGGING", "true").lower() == "true"

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not found. Install it with: pip install openai")

# Get model IDs from environment variables
OPENAI_TEXT_MODEL = os.environ.get("OPENAI_TEXT_MODEL", "gpt-4-turbo")
OPENAI_VISION_MODEL = os.environ.get("OPENAI_VISION_MODEL", "gpt-4-vision-preview")

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken not found. Install it with: pip install tiktoken")


def log_llm_prompt(
    company_name: str, 
    phase: str, 
    section: str, 
    messages: List[Dict[str, Any]],
    model: str,
    temperature: float,
    max_tokens: int,
    run_timestamp: Optional[str] = None
) -> None:
    """Log the prompt sent to the LLM.
    
    Args:
        company_name: Name of the company
        phase: Phase of processing (e.g., 'report_generation')
        section: Section being generated (e.g., 'executive_summary')
        messages: Messages sent to the LLM
        model: Model name
        temperature: Temperature setting
        max_tokens: Max tokens setting
        run_timestamp: Optional timestamp to use for the log filename. If provided, 
                       appends to an existing log file with this timestamp.
    """
    if not ENABLE_LOGGING:
        logger.info("LLM logging is disabled. Skipping log entry.")
        return
    
    # Create logs directory
    company_logs_dir = Path(f"company_data/{company_name}/logs")
    company_logs_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate timestamp for the log file or use provided one
    timestamp = run_timestamp if run_timestamp else datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{company_name}_{phase}_{timestamp}.log"
    log_path = company_logs_dir / log_filename
    
    # Prepare log entry
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "company": company_name,
        "phase": phase,
        "section": section,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": messages
    }
    
    # Append to log file
    try:
        # Create file if it doesn't exist
        if not log_path.exists():
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(f"# LLM Interaction Log for {company_name}\n")
                f.write(f"# Phase: {phase}\n")
                f.write(f"# Created: {timestamp}\n\n")
        
        # Append log entry
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n## {section} - {datetime.datetime.now().isoformat()}\n")
            f.write(json.dumps(log_entry, indent=2))
            f.write("\n\n---\n\n")
        
        logger.info(f"Logged LLM prompt for {company_name}/{phase}/{section} to {log_path}")
    except Exception as e:
        logger.error(f"Failed to log LLM prompt: {str(e)}")


def extract_prompt_sections(template_path: str) -> Tuple[str, str]:
    """Extract system and user prompts from template file.

    Args:
        template_path: Path to the template markdown file

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Extract system prompt
    system_pattern = r"## System Prompt\s*\n\s*(.*?)(?=\s*##|$)"
    system_match = re.search(system_pattern, template_content, re.DOTALL)
    system_prompt = system_match.group(1).strip() if system_match else ""
    
    # Extract user prompt
    user_pattern = r"## User Prompt\s*\n\s*(.*?)(?=\s*##|$)"
    user_match = re.search(user_pattern, template_content, re.DOTALL)
    user_prompt = user_match.group(1).strip() if user_match else ""
    
    return system_prompt, user_prompt


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count the number of tokens in a text string.

    Args:
        text: The text to count tokens for
        model: The model to count tokens for

    Returns:
        Token count
    """
    if not TIKTOKEN_AVAILABLE:
        # Approximate token count if tiktoken not available
        return len(text) // 4
    
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception as e:
        logger.error(f"Error counting tokens: {str(e)}")
        return len(text) // 4


def chunk_text(text: str, max_tokens: int = 4000) -> List[str]:
    """Split text into chunks that fit within token limits.

    Args:
        text: Text to chunk
        max_tokens: Maximum tokens per chunk

    Returns:
        List of text chunks
    """
    # Split by markdown sections (## or ###)
    section_pattern = r'((?:^|\n)#{2,3}\s+[^\n]+)'
    sections = re.split(section_pattern, text)
    
    # Recombine sections with their headers
    chunks = []
    current_chunk = ""
    
    for i in range(0, len(sections)):
        section = sections[i]
        
        # Check if adding this section exceeds the token limit
        combined = current_chunk + section
        if count_tokens(combined) > max_tokens and current_chunk:
            chunks.append(current_chunk)
            current_chunk = section
        else:
            current_chunk = combined
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    # If some chunks are still too large, split by paragraphs
    result = []
    for chunk in chunks:
        if count_tokens(chunk) > max_tokens:
            paragraphs = chunk.split("\n\n")
            current_chunk = ""
            
            for para in paragraphs:
                if count_tokens(current_chunk + para + "\n\n") > max_tokens and current_chunk:
                    result.append(current_chunk)
                    current_chunk = para + "\n\n"
                else:
                    current_chunk += para + "\n\n"
                    
            if current_chunk:
                result.append(current_chunk)
        else:
            result.append(chunk)
    
    # Print the total number of chunks
    logger.info(f"Chunking complete. Total chunks: {len(result)}")
    
    return result


def generate_report(
    master_file_path: str,
    template_path: str,
    output_dir: Optional[str] = None,
    model: Optional[str] = None
) -> str:
    """Generate an equity research report from a master file.

    Args:
        master_file_path: Path to the master markdown file
        template_path: Path to the template markdown file
        output_dir: Directory to save the report (defaults to same as master file)
        model: LLM model to use for generation (defaults to OPENAI_TEXT_MODEL from env)

    Returns:
        Path to the generated report
    """
    if not OPENAI_AVAILABLE:
        logger.error("OpenAI library is required for report generation")
        return ""
    
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set")
        return ""
    
    logger.info(f"Generating report from master file: {master_file_path}")
    
    # Get model from environment if not specified
    if model is None:
        model = OPENAI_TEXT_MODEL  # Use the global variable
        logger.info(f"Using model from environment: {model}")
    
    # Load master file content
    try:
        with open(master_file_path, 'r', encoding='utf-8') as f:
            master_content = f.read()
    except Exception as e:
        logger.error(f"Error reading master file: {str(e)}")
        return ""
    
    # Extract company name from master file path
    file_name = Path(master_file_path).stem  # e.g., company_master_timestamp
    company_name = file_name.split('_master_')[0] if '_master_' in file_name else file_name
    
    # Determine output directory
    if output_dir is None:
        output_dir = Path(master_file_path).parent
    
    # Create timestamp for the report
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"{company_name}_equity_research_{timestamp}.md"
    output_path = Path(output_dir) / report_filename
    
    # Create a unique log file for this run
    run_timestamp = timestamp  # Use the same timestamp for the entire run
    log_filename = f"{company_name}_report_generation_{run_timestamp}.log"
    
    # Get prompts from template
    system_prompt, user_prompt = extract_prompt_sections(template_path)
    
    if not system_prompt or not user_prompt:
        logger.error("Failed to extract prompts from template")
        return ""
    
    # Replace placeholders
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    system_prompt = system_prompt.replace("{company}", company_name).replace("{timestamp}", current_datetime)
    user_prompt = user_prompt.replace("{company}", company_name).replace("{timestamp}", current_datetime)
    
    # Improved approach for handling content:
    # 1. First chunk the master content into sections
    sections = extract_semantic_sections(master_content)
    
    # 2. Process sections with appropriate context
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    
    # Define phase for logging
    phase = "report_generation"
    
    # Generate a structured report in parts
    report_components = {
        "executive_summary": None,
        "business_overview": None,
        "financial_analysis": None,
        "competitive_landscape": None,
        "growth_prospects": None,
        "risks": None,
        "conclusion": None
    }
    
    # 3. First generate a high-level summary of the entire document to provide context
    logger.info("Generating high-level summary of the master document")
    summary_chunks = chunk_text(master_content, max_tokens=7000)  # Larger chunks for summary
    summary_content = []
    
    for i, chunk in enumerate(summary_chunks):
        try:
            messages = [
                {"role": "system", "content": "You are a financial analyst summarizing key information about a company. Provide only the factual information from the document without analysis or conclusions."},
                {"role": "user", "content": f"Summarize the key information about {company_name} from this document, focusing on extracting factual data:\n\n{chunk}"}
            ]
            
            # Log the prompt
            log_llm_prompt(
                company_name=company_name,
                phase=phase,
                section=f"document_summary_chunk_{i+1}",
                messages=messages,
                model=model,
                temperature=0.2,
                max_tokens=1500,
                run_timestamp=run_timestamp
            )
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
                max_tokens=1500
            )
            summary_content.append(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
    
    document_summary = "\n\n".join(summary_content)
    
    # 4. Now generate each section of the report with the overall context
    logger.info("Generating report sections with document context")
    
    # Executive Summary
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Based on the following summary of information about {company_name}, write ONLY the Executive Summary section of an equity research report: \n\n{document_summary}"}
        ]
        
        # Log the prompt
        log_llm_prompt(
            company_name=company_name,
            phase=phase,
            section="executive_summary",
            messages=messages,
            model=model,
            temperature=0.3,
            max_tokens=1000,
            run_timestamp=run_timestamp
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )
        report_components["executive_summary"] = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating executive summary: {str(e)}")
        report_components["executive_summary"] = f"## Executive Summary\n\nError generating content: {str(e)}"
    
    # Business Overview
    try:
        # Find the most relevant chunks for business overview
        business_content = extract_content_for_section(sections, ["business", "company", "overview", "product", "service"])
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Based on the following information about {company_name}, write ONLY the Business Overview section of an equity research report. Focus on the company's products, services, market position, and business model: \n\n{business_content}"}
        ]
        
        # Log the prompt
        log_llm_prompt(
            company_name=company_name,
            phase=phase,
            section="business_overview",
            messages=messages,
            model=model,
            temperature=0.3,
            max_tokens=1500,
            run_timestamp=run_timestamp
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=1500
        )
        report_components["business_overview"] = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating business overview: {str(e)}")
        report_components["business_overview"] = f"## Business Overview\n\nError generating content: {str(e)}"
    
    # Financial Analysis
    try:
        financial_content = extract_content_for_section(sections, ["financial", "revenue", "profit", "margin", "growth", "income", "balance", "cash flow"])
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Based on the following financial information about {company_name}, write ONLY the Financial Analysis section of an equity research report. Focus on revenue trends, profitability, balance sheet strength, and cash flow: \n\n{financial_content}"}
        ]
        
        # Log the prompt
        log_llm_prompt(
            company_name=company_name,
            phase=phase,
            section="financial_analysis",
            messages=messages,
            model=model,
            temperature=0.3,
            max_tokens=2000,
            run_timestamp=run_timestamp
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=2000
        )
        report_components["financial_analysis"] = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating financial analysis: {str(e)}")
        report_components["financial_analysis"] = f"## Financial Analysis\n\nError generating content: {str(e)}"
    
    # Competitive Landscape
    try:
        competitive_content = extract_content_for_section(sections, ["competition", "competitor", "market", "industry", "landscape", "peer", "swot", "strength"])
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Based on the following information about {company_name}'s competitive position, write ONLY the Competitive Landscape section of an equity research report: \n\n{competitive_content}"}
        ]
        
        # Log the prompt
        log_llm_prompt(
            company_name=company_name,
            phase=phase,
            section="competitive_landscape",
            messages=messages,
            model=model,
            temperature=0.3,
            max_tokens=1500,
            run_timestamp=run_timestamp
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=1500
        )
        report_components["competitive_landscape"] = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating competitive landscape: {str(e)}")
        report_components["competitive_landscape"] = f"## Competitive Landscape\n\nError generating content: {str(e)}"
    
    # Growth Prospects
    try:
        growth_content = extract_content_for_section(sections, ["growth", "future", "outlook", "expansion", "strategy", "opportunity", "initiative"])
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Based on the following information about {company_name}'s growth prospects, write ONLY the Growth Prospects and Future Outlook section of an equity research report: \n\n{growth_content}"}
        ]
        
        # Log the prompt
        log_llm_prompt(
            company_name=company_name,
            phase=phase,
            section="growth_prospects",
            messages=messages,
            model=model,
            temperature=0.3,
            max_tokens=1500,
            run_timestamp=run_timestamp
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=1500
        )
        report_components["growth_prospects"] = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating growth prospects: {str(e)}")
        report_components["growth_prospects"] = f"## Growth Prospects\n\nError generating content: {str(e)}"
    
    # Risks and Challenges
    try:
        risk_content = extract_content_for_section(sections, ["risk", "challenge", "threat", "regulation", "compliance", "issue", "problem", "concern"])
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Based on the following information about risks facing {company_name}, write ONLY the Risks and Challenges section of an equity research report: \n\n{risk_content}"}
        ]
        
        # Log the prompt
        log_llm_prompt(
            company_name=company_name,
            phase=phase,
            section="risks_challenges",
            messages=messages,
            model=model,
            temperature=0.3,
            max_tokens=1500,
            run_timestamp=run_timestamp
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=1500
        )
        report_components["risks"] = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating risks section: {str(e)}")
        report_components["risks"] = f"## Risks and Challenges\n\nError generating content: {str(e)}"
    
    # Conclusion
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Based on all the information provided about {company_name}, write ONLY a brief Conclusion section for an equity research report that summarizes the investment thesis: \n\n{document_summary}"}
        ]
        
        # Log the prompt
        log_llm_prompt(
            company_name=company_name,
            phase=phase,
            section="conclusion",
            messages=messages,
            model=model,
            temperature=0.3,
            max_tokens=1000,
            run_timestamp=run_timestamp
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )
        report_components["conclusion"] = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating conclusion: {str(e)}")
        report_components["conclusion"] = f"## Conclusion\n\nError generating content: {str(e)}"
    
    # 5. Assemble the final report
    final_report = [
        f"# Equity Research Report: {company_name.upper()}",
        f"Generated on: {current_datetime}",
        f"Based on data from: {Path(master_file_path).name}",
        "\n---\n"
    ]
    
    # Add each component in order
    if report_components["executive_summary"]:
        final_report.append(ensure_section_heading(report_components["executive_summary"], "Executive Summary", 1))
    
    if report_components["business_overview"]:
        final_report.append(ensure_section_heading(report_components["business_overview"], "Business Overview", 1))
    
    if report_components["financial_analysis"]:
        final_report.append(ensure_section_heading(report_components["financial_analysis"], "Financial Analysis", 1))
    
    if report_components["competitive_landscape"]:
        final_report.append(ensure_section_heading(report_components["competitive_landscape"], "Competitive Landscape", 1))
    
    if report_components["growth_prospects"]:
        final_report.append(ensure_section_heading(report_components["growth_prospects"], "Growth Prospects and Future Outlook", 1))
    
    if report_components["risks"]:
        final_report.append(ensure_section_heading(report_components["risks"], "Risks and Challenges", 1))
    
    if report_components["conclusion"]:
        final_report.append(ensure_section_heading(report_components["conclusion"], "Conclusion", 1))
    
    # Add metadata
    final_report.append("\n---\n")
    final_report.append("## Report Metadata")
    final_report.append(f"- Company: {company_name}")
    final_report.append(f"- Generation Date: {current_datetime}")
    final_report.append(f"- Master File: {Path(master_file_path).name}")
    final_report.append(f"- LLM Model: {model}")
    
    # Write the report
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n\n".join(final_report))
        logger.info(f"Report generated: {output_path}")
    except Exception as e:
        logger.error(f"Error writing report file: {str(e)}")
        return ""
    
    return str(output_path)


def extract_semantic_sections(content: str) -> Dict[str, str]:
    """Extract semantic sections from the master content.

    Args:
        content: The master file content

    Returns:
        Dictionary of section type to content
    """
    # Split by markdown headers
    header_pattern = r'(^|\n)#{1,3}\s+(.+?)(\n|$)'
    parts = re.split(header_pattern, content, flags=re.MULTILINE)
    
    sections = {}
    current_title = "General"
    current_content = ""
    
    for i in range(0, len(parts), 4):
        if i + 2 < len(parts):
            title = parts[i + 2].strip()
            if i + 3 < len(parts):
                content_part = parts[i + 3]
                if title.lower() not in sections:
                    sections[title.lower()] = content_part
                else:
                    sections[title.lower()] += "\n\n" + content_part
    
    return sections


def extract_content_for_section(sections: Dict[str, str], keywords: List[str]) -> str:
    """Extract content relevant for a specific section based on keywords.

    Args:
        sections: Dictionary of section titles to content
        keywords: List of keywords to match section titles against

    Returns:
        Combined content for the section
    """
    relevant_content = []
    
    for section_title, content in sections.items():
        if any(keyword.lower() in section_title.lower() for keyword in keywords):
            relevant_content.append(f"# {section_title.title()}\n\n{content}")
    
    # If no matching sections, include all content
    if not relevant_content:
        all_content = "\n\n".join([f"# {title.title()}\n\n{content}" for title, content in sections.items()])
        return all_content[:8000]  # Limit content if too large
    
    return "\n\n".join(relevant_content)


def ensure_section_heading(content: str, heading: str, level: int = 2) -> str:
    """Ensure the content has the proper section heading.

    Args:
        content: Section content
        heading: Expected heading
        level: Heading level (1-6)

    Returns:
        Content with proper heading
    """
    heading_prefix = "#" * level
    
    # Check if content already starts with the heading
    if content.strip().startswith(f"{heading_prefix} {heading}") or \
       content.strip().startswith(f"{heading_prefix} Executive Summary") or \
       content.strip().startswith(f"{heading_prefix} Business Overview") or \
       content.strip().startswith(f"{heading_prefix}Executive Summary") or \
       content.strip().startswith(f"{heading_prefix}Business Overview"):
        return content.strip()
    
    # Check if content starts with a different heading
    if re.match(r'^#{1,6}\s+', content.strip()):
        # Replace the first heading with our desired heading
        return re.sub(r'^#{1,6}\s+.*?(\n|$)', f"{heading_prefix} {heading}\n", content.strip(), count=1, flags=re.MULTILINE)
    
    # Content doesn't start with any heading, add one
    return f"{heading_prefix} {heading}\n\n{content.strip()}"