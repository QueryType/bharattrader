# FinInsightGPT: AI-Powered Investment Analysis

FinInsightGPT is an application that helps with investment decisions and business analysis by processing company data files, converting them to structured markdown, and generating comprehensive equity research reports using AI.

## Features

- **Document Processing**: Converts various file formats (PDF, DOCX, PPTX, TXT, XLSX, images) to markdown
- **Intelligent Image Analysis**: Uses OCR and AI vision to extract text and analyze charts/graphs
- **Master File Generation**: Consolidates all company documents into a comprehensive master file
- **AI Report Generation**: Creates detailed equity research reports using LLM models
- **Command-line Interface**: Easy-to-use CLI for all operations

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR (for image processing):
   - macOS: `brew install tesseract`
   - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
   - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

4. Set up your environment variables:
   - Copy the template file: `cp .env.example .env`
   - Edit the `.env` file and add your OpenAI API key and model preferences:

```
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# OpenAI Model IDs
OPENAI_TEXT_MODEL=gpt-4-turbo
OPENAI_VISION_MODEL=gpt-4-vision-preview
```

## Usage

### Directory Structure

Place company files in folders under `company_data`:

```
company_data/
  ├── company1/
  │   ├── file1.pdf
  │   ├── file2.txt
  │   └── image1.jpg
  └── company2/
      ├── presentation.pptx
      └── financials.xlsx
```

### Commands

#### List available companies:

```bash
python src/main.py list
```

#### Process files for a company:

```bash
python src/main.py process <company_folder>
```

#### Generate master file from processed files:

```bash
python src/main.py master <company_folder> [--output-dir <output_directory>]
```

#### Generate report from master file:

```bash
python src/main.py report <master_file> [--template <template_file>] [--output-dir <output_directory>] [--model <llm_model>]
```

#### Run the entire pipeline (process files, generate master, create report):

```bash
python src/main.py all <company_folder> [--template <template_file>] [--model <llm_model>]
```

### Examples

Process files for CDSL:

```bash
python src/main.py process cdsl
```

Generate a report for JyothyLabs using previously created master file:

```bash
python src/main.py report jyothylabs_master_20250504_123456.md --model gpt-4-vision-preview
```

Run the entire pipeline for a new company:

```bash
python src/main.py all mynewcompany --model gpt-4-turbo
```

## Report Templates

The system uses the template file in `prompt_master/Equity_Research_Report_Template.md` by default. This template contains:

1. A system prompt to instruct the AI model
2. A user prompt that defines the report structure and analysis requirements

You can modify this template or create custom templates for different analysis styles.

## Dependencies

- pymupdf: PDF processing
- python-docx: DOCX processing
- python-pptx: PowerPoint processing
- pandas & openpyxl: Excel processing
- Pillow & pytesseract: Image processing
- openai: AI model integration
- tiktoken: Token counting for LLM API calls