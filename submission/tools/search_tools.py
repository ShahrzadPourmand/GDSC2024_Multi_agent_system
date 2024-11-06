#import json
#import requests
#import boto3
from langchain.tools import tool
from crewai_tools import ScrapeWebsiteTool
import src.submission.tools.tables as pirls_tables

# List of pre-approved URLs
APPROVED_URLS = [
    'https://pirls2021.org/results/trends/overall',
    'https://pirls2021.org/results/context-school/socioeconomic-background',
    'https://pirls2021.org/results/context-home/socioeconomic-status'
]


@tool
def scrape_tool(url: str) -> str:
    """ Useful to search the PIRLS online documents on PIRLS websites.

    Args:
        url (str): The URL of the document. Here is the list of approved linkes with it's explanation:
        1. 'https://pirls2021.org/results/trends/overall' Provides information about Trends in Average Reading Achievement in PIRLS.
        2. 'https://pirls2021.org/results/context-school/socioeconomic-background' Details the correlation between the socioeconomic status of schoolsâ€™ student bodies and studentsâ€™ average reading achievement in PIRLS.
        3. 'https://pirls2021.org/results/context-home/socioeconomic-status' Provides information about Home Socioeconomic Status in PIRLS.

    Returns:
        str: The content of the document as a string, or an error message.

    Raises:
        Exception: If it encounters an exception during execution.
    """
    if url not in APPROVED_URLS:
        return f"Error: The URL '{url}' is not approved for scraping. Please provide a valid, pre-approved URL."

    try:
        # Initialize the scraping tool and fetch the data
        tool = ScrapeWebsiteTool(url)
        text = tool.run()
        return text

    except Exception as e:
        # Return a helpful error message instead of raising the exception
        return f"An error occurred while scraping the website: {str(e)}"


@tool
def get_PIRLS_tables(table_type: str) -> str:
    """ 
    Retrieves the specified table, either PIRLS average reading trend or GNI per Capita.
    

    Args:
        table_type: Specifies the type of table to retrieve must be one of the following:
        1. "avg_readings":  to get the PIRLS table about "Trend of Average Reading Achievement (Fourth Grade)" which contains average reading achievements of different countries across various years. Example data: Australia: 2021 (During COVID-19): 540, 2016: 544, 2011: 527.
        2. "gni": Retrieves the table listing each country and its corresponding Gross National Income (GNI) per capita in PIRLS 2021, which is often closely correlated with GDP.  Example data: Australia: 53680.

    Returns:
        str: A formatted string containing the requested table or an error message.
    """
    try:
        result = ""
        if table_type.lower() == "avg_readings":
            result += "Trend of Average Reading Achievement (Fourth Grade)\n"
            result += "Assessed During COVID-19 pandemic and Prior (Because of rounding some results may appear inconsistent!)\n"
            result += "The document is downloaded from https://pirls2021.org/results \n"
            # Append PIRLS data
            for country, data in pirls_tables.pirls_trends_avg_reading.items():
                result += f"{country}: ["  # Start the line with the country name
                result += ", ".join([f"{year}: {score}" for year, score in data.items()])# Combine year and score
                result += "]\n"  # End the line for each country

        # Handle the GNI data request
        elif table_type.lower() == "gni":
            gni_data = pirls_tables.pirls_countries_2021_gni_per_capita
            result += "\nGNI per Capita Data\n"
            result += "The document is downloaded from: https://pirls2021.org/encyclopedia/ \n"

            # Append GNI data
            for country, gni in gni_data.items():
                result += f"Country: {country}, GNI per Capita: {gni} USD\n"

        else:
            return "Invalid table type specified. Use 'avg_readings' or 'gni'."

    except Exception as e:
        return f"An error occurred while retrieving data: {str(e)}"

    return result.strip()  # Strip to remove any trailing new lines
    
    


