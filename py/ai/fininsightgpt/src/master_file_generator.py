"""
Master File Generator Module

This module handles the creation of the consolidated master markdown file from individual markdown files.
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Optional
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_master_file(
    company_name: str,
    markdown_files: List[str],
    output_dir: Optional[str] = None
) -> str:
    """Generate a consolidated master markdown file for a company.

    Args:
        company_name: Name of the company
        markdown_files: List of paths to markdown files to include
        output_dir: Directory to save the master file (defaults to company folder)

    Returns:
        Path to the generated master file
    """
    logger.info(f"Generating master file for {company_name} from {len(markdown_files)} markdown files")
    
    # Create timestamp for the master file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    master_filename = f"{company_name}_master_{timestamp}.md"
    
    # Determine output directory
    if output_dir is None:
        # Try to infer from the first markdown file
        if markdown_files:
            first_file = Path(markdown_files[0])
            output_dir = first_file.parent.parent  # Go up one level from processed/
        else:
            output_dir = os.getcwd()
    
    output_path = Path(output_dir) / master_filename
    
    # Prepare master file content
    master_content = [
        f"# {company_name.upper()} - Consolidated Analysis",
        f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Number of source documents: {len(markdown_files)}",
        "\n---\n"
    ]
    
    # Table of Contents
    toc = ["## Table of Contents"]
    
    # Track sections for organizing content
    sections = {
        "Financial Data": [],
        "Business Overview": [],
        "Management": [],
        "Industry Analysis": [],
        "News & Media": [],
        "Miscellaneous": []
    }
    
    # Process each markdown file
    for idx, md_file in enumerate(markdown_files):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract filename for reference
            filename = Path(md_file).stem
            
            # Determine section based on content keywords
            section = "Miscellaneous"
            content_lower = content.lower()
            
            if any(kw in content_lower for kw in ["profit", "revenue", "financial", "balance sheet", "income", "statement", "ratio"]):
                section = "Financial Data"
            elif any(kw in content_lower for kw in ["business", "product", "service", "segment", "overview"]):
                section = "Business Overview"
            elif any(kw in content_lower for kw in ["ceo", "director", "management", "board"]):
                section = "Management"
            elif any(kw in content_lower for kw in ["industry", "market", "competitor", "competition"]):
                section = "Industry Analysis"
            elif any(kw in content_lower for kw in ["news", "press", "announcement", "media"]):
                section = "News & Media"
            
            # Add to appropriate section
            sections[section].append((filename, content))
            
            # Add to TOC
            toc.append(f"- [{filename}](#{filename.lower().replace(' ', '-')})")
            
        except Exception as e:
            logger.error(f"Error processing markdown file {md_file}: {str(e)}")
            sections["Miscellaneous"].append((
                f"Error_{idx}",
                f"Error processing file {md_file}: {str(e)}"
            ))
    
    # Add TOC to master content
    master_content.extend(toc)
    master_content.append("\n---\n")
    
    # Add content by section
    for section_name, section_contents in sections.items():
        if section_contents:
            master_content.append(f"# {section_name}")
            
            for filename, content in section_contents:
                # Add section anchor
                master_content.append(f"<a id='{filename.lower().replace(' ', '-')}'></a>")
                
                # Clean up the content by removing the first heading if it matches the filename
                # This avoids duplication with our added heading
                content_lines = content.split("\n")
                if len(content_lines) > 0 and content_lines[0].startswith("# ") and filename in content_lines[0]:
                    content = "\n".join(content_lines[1:])
                
                master_content.append(f"## {filename}")
                master_content.append(content)
                master_content.append("\n---\n")
    
    # Add metadata and summary section
    master_content.append("# Metadata")
    master_content.append("## Document Sources")
    
    sources_table = ["| Source | Type | Date Included |"]
    sources_table.append("| --- | --- | --- |")
    
    for md_file in markdown_files:
        file_path = Path(md_file)
        file_type = file_path.suffix
        file_date = datetime.datetime.fromtimestamp(os.path.getmtime(md_file)).strftime('%Y-%m-%d')
        sources_table.append(f"| {file_path.stem} | {file_type} | {file_date} |")
    
    master_content.extend(sources_table)
    
    # Write the master file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n\n".join(master_content))
        logger.info(f"Master file generated: {output_path}")
    except Exception as e:
        logger.error(f"Error writing master file: {str(e)}")
        return ""
    
    return str(output_path)