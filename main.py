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
    # Replace '/edit' with '/gviz/tq?tqx=out:csv' to get the CSV format
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

def process_leads_data(df):
    """
    Process the leads DataFrame to extract necessary information.
    
    Args:
        df (DataFrame): The input DataFrame containing leads data.
    
    Returns:
        DataFrame: A processed DataFrame ready for SMS contacts.
    """
    
    # Normalize column names: strip whitespace and convert to lowercase
    df.columns = df.columns.str.strip().str.lower()
    
    # Ensure only single-word first and last names
    df['first name'] = df.get('first name', pd.Series([""] * len(df))).apply(lambda x: x.split()[0] if isinstance(x, str) and x else "")
    df['last name'] = df.get('last name', pd.Series([""] * len(df))).apply(lambda x: x.split()[0] if isinstance(x, str) and x else "")
    
    # Ensure unique emails
    df['email'] = df.get('email', pd.Series([""] * len(df))).astype(str).str.strip()
    df.drop_duplicates(subset='email', keep='first', inplace=True)
    
    # Handle mobile phone numbers
    df['mobile phone'] = df.get('mobile phone', pd.Series([""] * len(df))).astype(str).str.strip()
    df.drop_duplicates(subset='mobile phone', keep='first', inplace=True)
    
    # Clean up Address field
    df['address'] = df.get('address', pd.Series([""] * len(df))).astype(str).str.strip()

    # Extract City from the 'city, state zip code' column and convert to string
    if 'city, state zip code' in df.columns:
        df['city'] = df['city, state zip code'].astype(str).str.strip()
        
    # Extract State and Zip Code from 'unnamed: 6' and 'unnamed: 7' columns and convert to string
    df['state'] = df.get('unnamed: 6', pd.Series([""] * len(df))).astype(str).str.strip()
    df['zip code'] = df.get('unnamed: 7', pd.Series([""] * len(df))).astype(str).str.strip()

    # Create the output DataFrame
    output_df = pd.DataFrame({
        'First Name': df['first name'],
        'Last Name': df['last name'],
        'Email': df['email'],
        'Mobile Phone': df['mobile phone'],
        'Address': df['address'],
        'City': df['city'],
        'State': df['state'],
        'Zip Code': df['zip code']
    })
    
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

            # Generate output filename based on sheet name (for this example, we use "processed")
            output_filename = f"processed_leads.csv"

            # Create a download button for the processed CSV
            csv_buffer = io.StringIO()
            processed_data.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)

            # Convert StringIO content to bytes
            csv_bytes = csv_buffer.getvalue().encode('utf-8')

            st.download_button(
                label="Download Processed SMS Contacts",
                data=csv_bytes,
                file_name=output_filename,
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

            # Generate output filename based on sheet name (for this example, we use "processed")
            output_filename = f"processed_leads.csv"

            # Create a download button for the processed CSV
            csv_buffer = io.StringIO()
            processed_data.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)

            # Convert StringIO content to bytes
            csv_bytes = csv_buffer.getvalue().encode('utf-8')

            st.download_button(
                label="Download Processed SMS Contacts",
                data=csv_bytes,
                file_name=output_filename,
                mime='text/csv'
            )
        
        except Exception as e:
            st.error(f"An error occurred while processing the file: {e}")

if __name__ == "__main__":
    main()