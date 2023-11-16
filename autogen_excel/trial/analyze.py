import os
import pandas as pd
import openai
import time
import sys

# Set up Azure OpenAI configuration
def setup_openai():
    openai.api_type = "azure"
    openai.api_key = os.getenv("AZURE_OPENAI_KEY")
    openai.api_base = os.getenv("AZURE_OPENAI_BASE")
    openai.api_version = "2023-05-15"

# Read an Excel file and return a DataFrame
def read_excel_file(file_path):
    return pd.read_excel(file_path)

# Make a query to Azure OpenAI and handle rate limits
def query_azure_openai(row_data):
    system_content = read_system_content()
    messages = create_messages(system_content, row_data)
    
    response = safe_openai_call(
        openai.ChatCompletion.create,
        engine="gpt-4",
        messages=messages,
        temperature=0,
        max_tokens=8000,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    return response.choices[0].message['content'].strip()

# Read system content from a text file
def read_system_content():
    with open("system_content.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

# Create messages for OpenAI query
def create_messages(system_content, row_data):
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": row_data}
    ]

# Handle OpenAI API calls safely with retry on RateLimitError
def safe_openai_call(call_function, *args, **kwargs):
    try:
        return call_function(*args, **kwargs)
    except openai.error.RateLimitError:
        wait_time = 60
        print(f"Rate limit exceeded, waiting for {wait_time} seconds.")
        time.sleep(wait_time)
        return safe_openai_call(call_function, *args, **kwargs)

# Main processing function
def main(excel_file_path):
    df = read_excel_file(excel_file_path)
    output_file_path = create_output_file_path(excel_file_path)

    with open(output_file_path, 'w') as output_file:
        for index, row in df.iterrows():
            row_data_str = process_row(df, row)
            if row_data_str:
                response_text = query_azure_openai(row_data_str)
                print(response_text)  # For debugging; remove or comment out in production
                output_file.write(response_text + '\n')

# Process each row of the DataFrame
def process_row(df, row):
    row_data_list = [f"{column}: {row[column]}" for column in df.columns if not pd.isna(row[column])]
    return "決定金額は2,000,000円の場合は、" + ', '.join(row_data_list)

# Create the output file path
def create_output_file_path(excel_file_path):
    base_name = os.path.basename(excel_file_path).split('.')[0]
    directory = os.path.dirname(excel_file_path)
    return os.path.join(directory, base_name + '.txt')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <Excel File Path>")
        sys.exit(1)
    
    setup_openai()
    main(sys.argv[1])
