#!/usr/bin/env python3
"""
FinInsightGPT - AI-Powered Investment Analysis Application

This application processes company data files, converts them to markdown,
creates consolidated master files, and generates equity research reports.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load variables from .env file
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

# Import local modules
from document_processor import process_company_folder
from master_file_generator import generate_master_file
from report_generator import generate_report


def setup_argparse() -> argparse.ArgumentParser:
    """Set up command-line arguments."""
    parser = argparse.ArgumentParser(
        description="FinInsightGPT - AI-Powered Investment Analysis Application"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process files in a company folder')
    process_parser.add_argument('company_folder', help='Path to the company folder')
    
    # Master file command
    master_parser = subparsers.add_parser('master', help='Generate master file from processed files')
    master_parser.add_argument('company_folder', help='Path to the company folder')
    master_parser.add_argument('--output-dir', help='Directory to save the master file (defaults to company folder)')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate report from master file')
    report_parser.add_argument('master_file', help='Path to the master markdown file')
    report_parser.add_argument('--template', help='Path to the report template (default: prompt_master/Equity_Research_Report_Template.md)')
    report_parser.add_argument('--output-dir', help='Directory to save the report (defaults to master file directory)')
    report_parser.add_argument('--model', help='LLM model to use (default: gpt-4-turbo)')
    
    # All-in-one command
    all_parser = subparsers.add_parser('all', help='Process everything end-to-end')
    all_parser.add_argument('company_folder', help='Path to the company folder')
    all_parser.add_argument('--template', help='Path to the report template (default: prompt_master/Equity_Research_Report_Template.md)')
    all_parser.add_argument('--model', default='gpt-4-turbo', help='LLM model to use (default: gpt-4-turbo)')
    
    # List companies command
    subparsers.add_parser('list', help='List all available company folders')
    
    return parser


def list_companies(base_path: str = "../company_data") -> List[str]:
    """List all company folders in the company_data directory."""
    base_path = Path(base_path)
    
    if not base_path.exists() or not base_path.is_dir():
        logger.error(f"Company data directory not found: {base_path}")
        return []
    
    companies = []
    
    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            companies.append(item.name)
    
    return companies


def run_process_command(args: argparse.Namespace) -> None:
    """Process files in a company folder."""
    company_folder = args.company_folder
    
    # Ensure path is absolute
    if not os.path.isabs(company_folder):
        script_dir = Path(__file__).parent.absolute()
        company_data_dir = script_dir.parent / "company_data"
        company_folder = os.path.join(company_data_dir, company_folder)
    
    logger.info(f"Processing files in: {company_folder}")
    processed_files = process_company_folder(company_folder)
    
    if not processed_files:
        logger.warning("No files were processed.")
    else:
        logger.info(f"Successfully processed {len(processed_files)} files.")


def run_master_command(args: argparse.Namespace) -> Optional[str]:
    """Generate master file from processed files."""
    company_folder = args.company_folder
    output_dir = args.output_dir
    
    # Ensure path is absolute
    if not os.path.isabs(company_folder):
        script_dir = Path(__file__).parent.absolute()
        company_data_dir = script_dir.parent / "company_data"
        company_folder = os.path.join(company_data_dir, company_folder)
    
    # Get company name from folder path
    company_name = Path(company_folder).name
    
    # Find processed markdown files
    processed_folder = Path(company_folder) / "processed"
    
    if not processed_folder.exists() or not processed_folder.is_dir():
        logger.error(f"Processed folder not found: {processed_folder}")
        return None
    
    markdown_files = []
    for file in processed_folder.glob("*.md"):
        if file.is_file():
            markdown_files.append(str(file))
    
    if not markdown_files:
        logger.error("No processed markdown files found.")
        return None
    
    logger.info(f"Found {len(markdown_files)} processed files.")
    
    # Generate master file
    master_file_path = generate_master_file(
        company_name=company_name,
        markdown_files=markdown_files,
        output_dir=output_dir
    )
    
    if master_file_path:
        logger.info(f"Successfully generated master file: {master_file_path}")
    else:
        logger.error("Failed to generate master file.")
    
    return master_file_path


def run_report_command(args: argparse.Namespace) -> Optional[str]:
    """Generate report from master file."""
    master_file = args.master_file
    template_path = args.template
    output_dir = args.output_dir
    model = args.model
    
    # If model not specified in args, use the environment variable
    if model is None:
        model = os.environ.get("OPENAI_TEXT_MODEL", "gpt-4-turbo")
    
    # Ensure master file path is absolute
    if not os.path.isabs(master_file):
        script_dir = Path(__file__).parent.absolute()
        company_data_dir = script_dir.parent / "company_data"
        master_file = os.path.join(company_data_dir, master_file)
    
    # Ensure template path is set
    if template_path is None:
        script_dir = Path(__file__).parent.absolute()
        template_path = script_dir.parent / "prompt_master" / "Equity_Research_Report_Template.md"
    elif not os.path.isabs(template_path):
        script_dir = Path(__file__).parent.absolute()
        template_path = script_dir.parent / template_path
    
    # Check if files exist
    if not os.path.exists(master_file):
        logger.error(f"Master file not found: {master_file}")
        return None
    
    if not os.path.exists(template_path):
        logger.error(f"Template file not found: {template_path}")
        return None
    
    # Generate report
    report_file_path = generate_report(
        master_file_path=master_file,
        template_path=str(template_path),
        output_dir=output_dir,
        model=model
    )
    
    if report_file_path:
        logger.info(f"Successfully generated report: {report_file_path}")
    else:
        logger.error("Failed to generate report.")
    
    return report_file_path


def run_all_command(args: argparse.Namespace) -> None:
    """Process everything end-to-end: process files, generate master file, and generate report."""
    company_folder = args.company_folder
    template_path = args.template
    model = args.model
    
    # Process files
    process_args = argparse.Namespace(company_folder=company_folder)
    run_process_command(process_args)
    
    # Generate master file
    master_args = argparse.Namespace(company_folder=company_folder, output_dir=None)
    master_file_path = run_master_command(master_args)
    
    if not master_file_path:
        logger.error("Cannot continue without a master file.")
        return
    
    # Generate report
    report_args = argparse.Namespace(
        master_file=master_file_path,
        template=template_path,
        output_dir=None,
        model=model
    )
    report_file_path = run_report_command(report_args)
    
    if report_file_path:
        logger.info(f"End-to-end processing completed successfully.")
    else:
        logger.error("End-to-end processing failed during report generation.")


def check_environment():
    """Check if required environment variables are set."""
    if not os.environ.get("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY environment variable is not set. Set it in your .env file or export it in your shell.")
        return False
    return True


def main() -> None:
    """Main entry point of the application."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    elif args.command == 'process':
        run_process_command(args)
    
    elif args.command == 'master':
        run_master_command(args)
    
    elif args.command == 'report':
        run_report_command(args)
    
    elif args.command == 'all':
        run_all_command(args)
    
    elif args.command == 'list':
        script_dir = Path(__file__).parent.absolute()
        company_data_dir = script_dir.parent / "company_data"
        companies = list_companies(str(company_data_dir))
        
        if companies:
            print("Available company folders:")
            for company in companies:
                print(f"- {company}")
        else:
            print("No company folders found.")
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()