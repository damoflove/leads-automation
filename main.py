import streamlit as st
import pandas as pd
import io
import requests

def fetch_csv_from_url(url):
    """
    Fetch CSV data from a Google Sheets URL.
    
    Args:
        url (str): The Google Sheets URL.
    
    Returns:
        DataFrame: DataFrame containing the CSV data.
    """
    if 'docs.google.com' in url:
        csv_url = url.replace('/edit', '/gviz/tq?tqx=out:csv')
        response = requests.get(csv_url)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text))
        else:
            st.error("Failed to fetch data from the URL.")
            return None
    else:
        st.error("Invalid Google Sheets URL.")
        return None

def get_first_non_empty(row, column_prefix, max_columns=5):
    """
    Get the first non-empty value from columns with a common prefix.
    
    Args:
        row (Series): The input row.
        column_prefix (str): The prefix of the columns (e.g., 'email ', 'phone ').
        max_columns (int): Maximum number of columns to check.
    
    Returns:
        str: The first non-empty value found in the prefixed columns, or an empty string.
    """
    for i in range(1, max_columns + 1):
        column_name = f"{column_prefix}{i}"
        if column_name in row.index and pd.notna(row[column_name]):
            return row[column_name]
    return ""

def process_leads_data(df):
    """
    Process the leads DataFrame to extract necessary information.
    
    Args:
        df (DataFrame): The input DataFrame containing leads data.
    
    Returns:
        DataFrame: A processed DataFrame with duplicated rows for multiple wireless numbers.
    """
    
    # Normalize column names: strip whitespace and convert to lowercase
    df.columns = df.columns.str.strip().str.lower()

    # Identify columns for phones and types
    phone_columns = [col for col in df.columns if col.startswith('phone')]
    type_columns = [col for col in df.columns if col.startswith('phone type')]
    email_columns = [col for col in df.columns if col.startswith('email')]

    def extract_wireless_phones(row):
        """
        Extract only wireless phone numbers based on their corresponding type.
        """
        wireless_phones = []
        for phone_col, type_col in zip(phone_columns, type_columns):
            # Only add phone if type is 'wireless'
            if pd.notna(row[type_col]) and isinstance(row[type_col], str):
                if row[type_col].strip().lower() == 'wireless' and pd.notna(row[phone_col]):
                    wireless_phones.append(row[phone_col])
        return wireless_phones

    # Extract unique emails
    df['unique_emails'] = df[email_columns].apply(lambda row: row.dropna().unique().tolist(), axis=1)
    
    # Extract wireless phone numbers
    df['wireless_phones'] = df.apply(extract_wireless_phones, axis=1)

    # Generate output with multiple rows per wireless phone number and unique email
    output_rows = []
    for _, row in df.iterrows():
        wireless_phones = row['wireless_phones']
        unique_emails = row['unique_emails']
        
        # Ensure row duplication only when there are multiple wireless phones
        for i in range(len(wireless_phones)):
            output_rows.append({
                'First Name': row.get('firstname', ""),
                'Last Name': row.get('lastname', ""),
                'Email': unique_emails[i] if i < len(unique_emails) else "",
                'Mobile Phone': wireless_phones[i],
                'Address': row.get('propertyaddress', ""),
                'City': row.get('recipientcity', ""),
                'State': row.get('recipientstate', ""),
                'Zip Code': row.get('recipientpostalcode', "")
            })

    output_df = pd.DataFrame(output_rows)
    return output_df


def main():
    st.title("Leads CSV to SMS Contacts Converter")

    # Input for Google Sheets URL or raw CSV data
    url_input = st.text_input("Enter Google Sheets URL:")
    
    uploaded_file = st.file_uploader("Or upload your leads CSV file", type=["csv"])
    
    if url_input:
        # Fetch data from the provided URL
        raw_data = fetch_csv_from_url(url_input)
        
        if raw_data is not None:
            st.subheader("Raw Leads Data from URL")
            st.write(raw_data)
            
            # Process the leads data
            processed_data = process_leads_data(raw_data)

            # Create a download button for the processed CSV
            csv_buffer = io.StringIO()
            processed_data.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            csv_bytes = csv_buffer.getvalue().encode('utf-8')

            st.download_button(
                label="Download Processed SMS Contacts",
                data=csv_bytes,
                file_name="processed_leads.csv",
                mime='text/csv'
            )
        
    elif uploaded_file is not None:
        try:
            # Read the uploaded CSV file
            raw_data = pd.read_csv(uploaded_file)

            # Display the raw data for user reference
            st.subheader("Raw Leads Data")
            st.write(raw_data)

            # Process the leads data
            processed_data = process_leads_data(raw_data)

            # Create a download button for the processed CSV
            csv_buffer = io.StringIO()
            processed_data.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            csv_bytes = csv_buffer.getvalue().encode('utf-8')

            st.download_button(
                label="Download Processed SMS Contacts",
                data=csv_bytes,
                file_name="processed_leads.csv",
                mime='text/csv'
            )
        
        except Exception as e:
            st.error(f"An error occurred while processing the file: {e}")

if __name__ == "__main__":
    main()
