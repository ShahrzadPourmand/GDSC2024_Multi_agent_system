import boto3.session
from crewai_tools import tool
import pandas as pd
import matplotlib.pyplot as plt
from typing import Literal
import boto3
import io
from typing import List

VERSION = "v1"

@tool('generate_chart')
def generate_chart(chart_type: Literal['scatter','line','bar'], x_data: list, y_data: list, filename: str, x_axis: str, y_axis: str) -> str:
    """
    
    This function creates a chart using Seaborn and matplotlib, based on the specified
    chart type and input data. The resulting chart is saved as an image file. Ensure the x_data contains no more than 15 entries.

    Parameters:
    -----------
    chart_type : Literal['scatter', 'line', 'bar']
        The type of chart to generate. Must be one of 'scatter', 'line', or 'bar'.
    x_data : list
        A list containing the data to be plotted on the x-axis.
    y_data : list
        A list containing the data to be plotted on the y-axis.
    filename : str
        The name of the file (including path if necessary) where the chart image will be saved.
    x_axis : str
        The label for the x-axis.
    y_axis : str
        The label for the y-axis.

    Returns:
    --------
    str
        A message confirming that the chart has been saved, including the filename or an error message.
    """
    # Validate input lengths
    if len(x_data) != len(y_data):
        return "Error: x_data and y_data must have the same length."

    if len(x_data) == 0 or len(x_data) == 1:
        return "Error: x_data and y_data cannot be empty or one."

    if len(x_data) > 15:
        return "Error: Too many items to display. Ensure the x_data contains no more than 15 entries."

    filename = VERSION + filename
    # Convert input data to a pandas DataFrame and handle missing values
    df = pd.DataFrame({x_axis: x_data, y_axis: y_data}).dropna()

    # Set up the plot with a fixed size for clarity
    plt.figure(figsize=(8, 6))

    # Plot based on chart type
    if chart_type == "scatter":
        plt.scatter(df[x_axis], df[y_axis])

    elif chart_type == "line":
        plt.plot(df[x_axis], df[y_axis], marker='o')

    elif chart_type == "bar":
        plt.bar(df[x_axis], df[y_axis], color='skyblue')



        #Add value labels on top of bars if y_data is numeric
        for x, value in zip(df[x_axis], df[y_axis]):
            y_label = f'{int(value)}' if value == int(value) else f'{value:.2f}'
            plt.text(x, value, y_label, ha='center', va='bottom')

    else:
        return f"Error: Unsupported chart type: {chart_type}"
    # Set x-ticks to unique x values to avoid duplicate display
    plt.xticks(df[x_axis].unique())

    # Check the number of unique values in the x-axis data
    if len(df[x_axis].unique()) > 5:
        # Rotate x-axis labels 45 degrees if the x-axis data is numeric
        if pd.api.types.is_numeric_dtype(df[x_axis]):
            if len(df[x_axis].unique()) <= 10:
                plt.xticks(rotation=45)
        # Rotate 90 degrees if there are more than 10 unique numeric values
            else:
                plt.xticks(rotation=90)
        # Rotate x-axis labels 90 degrees if the x-axis data is text (categorical)
        else:
            plt.xticks(rotation=90)
    # Set labels and title
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(f"{chart_type.capitalize()} Chart: {y_axis} vs {x_axis}")

    # Ensure integer-only x-axis labels if all values are integers
    if all(isinstance(x, (int, float)) and x == int(x) for x in df[x_axis]):
        plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x)}'))

    # Add grid for better readability
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Adjust layout to avoid clipping the labels
    plt.tight_layout()

    # Save the plot to a BytesIO object
    img_data = io.BytesIO()
    plt.savefig(img_data, format='png', dpi=300, bbox_inches='tight')
    plt.close()

    # Reset the pointer of the BytesIO object
    img_data.seek(0)

    # Upload the image to S3
    session = boto3.Session()
    s3 = session.client('s3')
    bucket_name = ''
    try:
        s3.upload_fileobj(img_data, bucket_name, filename)
        # Build and return the S3 URL
        s3_url = f'https://{bucket_name}.s3.amazonaws.com/{filename}'
        return s3_url
    except Exception as e:
        return f"An error occurred: {str(e)}"


@tool('generate_pie_chart')
def generate_pie_chart(labels: List[str], values: List[float], filename: str, title: str) -> str:
    """
    This function creates a pie chart based on input labels and values. The resulting
    chart is saved as an image file. Limit the categories to 10 or fewer.
    Parameters:
    -----------
    labels : List[str]
        A list of category labels for each pie slice.
    values : List[float]
        A list of values corresponding to each category, determining slice sizes.
    filename : str
        The name of the file (including path if necessary) where the chart image will be saved.
    title : str
        The title of the pie chart.

    Returns:
    --------
    str
        A message confirming that the chart has been saved, including the filename or an error message.
    """
    # Validate input lengths
    if len(labels) != len(values):
        return "Error: labels and values must have the same length."

    if len(labels) == 0 or len(labels) == 1:
        return "Error: labels and values cannot be empty or contain only one value."
    
    if len(labels) > 10:
        return "Error: Too many items to display in a pie chart. Please limit to 10 or fewer categories."
    
    filename = VERSION + filename
    # Convert input data to a pandas DataFrame and handle missing values
    df = pd.DataFrame({'Label': labels, 'Value': values})

    # Set up the plot with a fixed size for clarity
    plt.figure(figsize=(8, 8))

    # Plot the pie chart
    plt.pie(df['Value'], labels=df['Label'], autopct='%1.1f%%', startangle=90, wedgeprops={'edgecolor': 'black'})
    plt.title(title)

    # Save the plot to a BytesIO object
    img_data = io.BytesIO()
    plt.savefig(img_data, format='png', dpi=300, bbox_inches='tight')
    plt.close()

    # Reset the pointer of the BytesIO object
    img_data.seek(0)

    # Upload the image to S3
    session = boto3.Session()
    s3 = session.client('s3')
    bucket_name = ''
    try:
        s3.upload_fileobj(img_data, bucket_name, filename)
        # Build and return the S3 URL
        s3_url = f'https://{bucket_name}.s3.amazonaws.com/{filename}'
        return s3_url
    except Exception as e:
        return f"An error occurred: {str(e)}"
