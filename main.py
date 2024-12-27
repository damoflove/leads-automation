import streamlit as st
import pandas as pd
import io
import requests

def fetch_csv_from_url(url):
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
    # Normalize column names to lowercase and strip whitespace
    df.columns = df.columns.str.strip().str.lower()

    # Ensure unique column names
    df.columns = pd.io.parsers.ParserBase({'names': df.columns})._maybe_dedup_names(df.columns)

    # Identify phone and phone type columns
    phone_columns = [col for col in df.columns if 'phone' in col and 'type' not in col]
    type_columns = [col for col in df.columns if 'phone type' in col]

    st.write("Detected Phone Columns:", phone_columns)
    st.write("Detected Phone Type Columns:", type_columns)

    # Handle mismatched column lengths
    if len(phone_columns) != len(type_columns):
        st.warning("Phone and Phone Type column counts do not match. Adjusting to minimum length.")
        min_length = min(len(phone_columns), len(type_columns))
        phone_columns = phone_columns[:min_length]
        type_columns = type_columns[:min_length]

    # Extract Wireless and VOIP phone numbers only
    def extract_selected_phones(row):
        selected_phones = []
        for phone_col, type_col in zip(phone_columns, type_columns):
            phone = row.get(phone_col, None)
            phone_type = row.get(type_col, None)

            # Ensure phone_type is a string and normalize
            phone_type = str(phone_type).strip().lower() if pd.notna(phone_type) else ""

            # Check for Wireless or VOIP and add phone number
            if phone and phone_type in ['wireless', 'voip']:
                selected_phones.append(str(phone).strip())

        return selected_phones

    # Extract unique emails
    email_columns = [col for col in df.columns if 'email' in col]
    df['unique_emails'] = df[email_columns].apply(lambda row: row.dropna().unique().tolist(), axis=1)

    # Add extracted phone numbers to the DataFrame
    df['selected_phones'] = df.apply(lambda row: extract_selected_phones(row), axis=1)

    # Prepare the output rows
    output_rows = []
    for idx, row in df.iterrows():
        selected_phones = row['selected_phones']
        unique_emails = row['unique_emails']

        # Ensure at least one output row per input row
        max_length = max(len(selected_phones), len(unique_emails), 1)
        for i in range(max_length):
            output_rows.append({
                'First Name': row.get('firstname', ""),
                'Last Name': row.get('lastname', ""),
                'Email': unique_emails[i] if i < len(unique_emails) else "",
                'Mobile Phone': selected_phones[i] if i < len(selected_phones) else "",
                'Address': row.get('propertyaddress', ""),
                'City': row.get('propertycity', ""),
                'State': row.get('propertystate', ""),
                'Zip Code': row.get('propertypostalcode', "")
            })

    return pd.DataFrame(output_rows)

def main():
    st.title("Leads CSV to SMS Contacts Converter")

    url_input = st.text_input("Enter Google Sheets URL:")
    uploaded_file = st.file_uploader("Or upload your leads CSV file", type=["csv"])
    
    if url_input:
        raw_data = fetch_csv_from_url(url_input)
        if raw_data is not None:
            st.subheader("Raw Leads Data from URL")
            st.write(raw_data)
            processed_data = process_leads_data(raw_data)
            csv_buffer = io.StringIO()
            processed_data.to_csv(csv_buffer, index=False)
            st.download_button("Download Processed SMS Contacts", data=csv_buffer.getvalue(), file_name="processed_leads.csv")
        
    elif uploaded_file:
        try:
            raw_data = pd.read_csv(uploaded_file)
            st.subheader("Raw Leads Data")
            st.write(raw_data)
            processed_data = process_leads_data(raw_data)
            csv_buffer = io.StringIO()
            processed_data.to_csv(csv_buffer, index=False)
            st.download_button("Download Processed SMS Contacts", data=csv_buffer.getvalue(), file_name="processed_leads.csv")
        except Exception as e:
            st.error(f"An error occurred while processing the file: {e}")

if __name__ == "__main__":
    main()
