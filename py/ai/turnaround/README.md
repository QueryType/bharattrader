# Business Turnaround Detection System

An AI-powered financial analysis tool that identifies potential business turnarounds by analyzing companies listed in a CSV file. The system uses advanced AI agents to research financial data and market conditions for each company, generating comprehensive markdown reports with turnaround potential verdicts.

## 🎯 Purpose

This tool is designed to help investors and analysts identify companies that may be experiencing business turnarounds by:
- Fetching latest financial reports and news
- Analyzing financial health indicators
- Determining turnaround potential with AI-driven insights
- Generating structured markdown reports for each company

## 📁 Project Structure

```
turnaround/
├── main.py                 # Main execution script
├── data/
│   └── financial_data.csv  # Input CSV with company data
├── my_tools/               # Custom tools for the AI agent
│   ├── __init__.py
│   ├── cmd_executor.py     # Shell command execution tool
│   ├── fs_reader.py        # File system reader tool
│   ├── markdown_report.py  # Report generation tool
│   └── web_fetcher.py      # Web search tool
├── output/                 # Generated reports directory
└── README.md              # This file
```

## 🔧 Prerequisites

Before running this project, ensure you have:

1. **Python 3.8+** installed
2. **OpenAI API Key** - Required for the AI agent
3. **Internet connection** - For web research functionality

## 📦 Installation & Setup

### 1. Install Required Dependencies

#### Option A: Using requirements.txt (Recommended)
```bash
pip install -r requirements.txt
```

#### Option B: Manual Installation
```bash
pip install smolagents python-dotenv openai litellm pandas numpy requests
```

### 2. Environment Configuration

Create a `.env` file in the project root directory:

```bash
touch .env
```

Add your OpenAI API key to the `.env` file:

```
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Prepare Input Data

Ensure your `data/financial_data.csv` file follows this format:

```csv
Name,BSE Code,NSE Code
63 Moons Tech.,526881,63MOONS
Apex Frozen Food,540692,APEX
Arman Financial,531179,ARMANFIN
```

**Required Columns:**
- `Name`: Company name (required)
- `BSE Code`: Bombay Stock Exchange code (optional)
- `NSE Code`: National Stock Exchange code (optional)

### 4. Create Output Directory

```bash
mkdir -p output
```

## 🚀 Usage

### Basic Execution

Run the turnaround analysis:

```bash
cd /path/to/turnaround
python main.py
```

### What Happens During Execution

1. **Data Loading**: Reads companies from `data/financial_data.csv`
2. **AI Analysis**: For each company, the AI agent:
   - Searches web for latest financial reports
   - Gathers recent news and market data
   - Analyzes financial health indicators
   - Determines turnaround potential
3. **Report Generation**: Creates detailed markdown reports in the `output/` directory

### Sample Output

Reports are saved as: `output/{business_name}{timestamp}_report.md`

Each report includes:
- **Business Name & Codes**
- **Summary of Financial Data**
- **Analysis of Financial Health**
- **Turnaround Potential Verdict**: "Strong Turnaround", "Weak Turnaround", or "No Turnaround"

## 🔧 Configuration

### Model Configuration

The system uses OpenAI's GPT-4.1-mini by default. To change the model, modify the `model` variable in `main.py`:

```python
model = LiteLLMModel(model_id="openai/gpt-4-turbo", api_key=os.getenv("OPENAI_API_KEY"))
```

### Analysis Steps

The AI agent follows these steps:
1. Company identification and code mapping
2. Web research for financial data and news
3. Financial health analysis
4. Turnaround potential assessment
5. Report generation and saving

## 📊 Best Practices

### When to Run
- **Ideal timing**: After quarterly earnings season
- **Frequency**: Quarterly or semi-annually for best results
- **Market conditions**: Consider running during market downturns for maximum turnaround identification

### Data Quality
- Ensure company names and stock codes are accurate
- Remove delisted or defunct companies from the CSV
- Update the CSV with new companies of interest

## 🛠️ Troubleshooting

### Common Issues

1. **Missing API Key**
   ```
   Error: OpenAI API key not found
   Solution: Check your .env file and ensure OPENAI_API_KEY is set
   ```

2. **CSV File Not Found**
   ```
   Error: The financial data file data/financial_data.csv does not exist
   Solution: Ensure the CSV file exists in the data/ directory
   ```

3. **Network Issues**
   ```
   Error: Web search failed
   Solution: Check internet connection and API quotas
   ```

4. **Permission Errors**
   ```
   Error: Cannot write to output directory
   Solution: Ensure output/ directory exists and has write permissions
   ```

### Debugging

Enable verbose logging by modifying the agent configuration:

```python
response = agent.run(final_instructions, max_steps=20, verbose=True)
```

## 📈 Output Interpretation

### Turnaround Verdicts

- **Strong Turnaround**: Company shows clear signs of recovery with improving fundamentals
- **Weak Turnaround**: Some positive indicators but recovery uncertain
- **No Turnaround**: No significant improvement indicators found

### Report Sections

Each generated report contains:
- Executive summary with verdict
- Financial metrics analysis
- Market sentiment and news analysis
- Risk factors and considerations
- Timeline for potential recovery

## 🤝 Contributing

To enhance this tool:
1. Add new analysis tools in the `my_tools/` directory
2. Extend the financial metrics analysis
3. Improve web scraping capabilities
4. Add visualization features

## ⚠️ Disclaimer

This tool is for informational purposes only and should not be considered as financial advice. Always conduct thorough due diligence and consult with financial professionals before making investment decisions.

## 📝 License

This project is part of the BharatTrader stock analysis suite. Please refer to the main project license for usage terms.
