from smolagents import tool
import datetime

instructions = """You are simple file writer tool that dumps the input text into a file."""

@tool
def save_report(md_report: str, business_name: str) -> None:
    """
    This tool saves a markdown formatted report to a file.
    Args:
        md_report (str): The markdown report content to save.
        business_name (str): The name of the business for which the report is generated.
    Returns:
        None: The function does not return anything, but saves the report to a file.
    """
    # check if the file exists on the filesystem
    if not md_report:
        return "No file path provided."
    
    output_file = f"output/{business_name}" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_report.md"

    # Save the output to a file
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(md_report)
    except Exception as e:
        return f"An error occurred while saving the report: {str(e)}"