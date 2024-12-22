import streamlit as st
import pandas as pd
import io
import requests

def fetch_csv_from_url(url):
    if 'docs.google.com' in url:
        csv_url = url.replace('/edit', '/gviz/tq?tqx=out:csv')
        response = requests.get(csv_url, stream=True)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text))
        else:
            st.error("Failed to fetch data from the URL.")
            return None
    else:
        st.error("Invalid Google Sheets URL.")
        return None

def process_chunk(chunk, phone_columns, type_columns, email_columns):
    # Extract wireless/VOIP phone numbers
    def extract_selected_phones(row):
        selected_phones = []
        for phone_col, type_col in zip(phone_columns, type_columns):
            if (
                type_col in row.index
                and pd.notna(row[type_col])
                and isinstance(row[type_col], str)
                and row[type_col].strip().lower() in ['wireless', 'voip']
                and phone_col in row.index
                and pd.notna(row[phone_col])
            ):
                selected_phones.append(str(row[phone_col]).strip())
        return selected_phones

    # Extract unique emails
    def extract_unique_emails(row):
        emails = [
            row[col].strip()
            for col in email_columns
            if col in row.index and pd.notna(row[col]) and isinstance(row[col], str)
        ]
        return list(pd.unique(emails))

    chunk['selected_phones'] = chunk.apply(extract_selected_phones, axis=1)
    chunk['unique_emails'] = chunk.apply(extract_unique_emails, axis=1)

    output_rows = []
    for _, row in chunk.iterrows():
        phones = row['selected_phones']
        emails = row['unique_emails']
        max_len = max(len(phones), len(emails))

        for i in range(max_len):
            output_rows.append({
                'First Name': row.get('firstname', ""),
                'Last Name': row.get('lastname', ""),
                'Email': emails[i] if i < len(emails) else "",
                'Mobile Phone': phones[i] if i < len(phones) else "",
                'Address': row.get('propertyaddress', ""),
                'City': row.get('propertycity', ""),
                'State': row.get('propertystate', ""),
                'Zip Code': row.get('propertypostalcode', "")
            })

    return output_rows

def process_large_file(file):
    chunksize = 10_000  # Adjust chunk size based on your memory capacity
    processed_data = []
    
    # Read the file in chunks
    for chunk in pd.read_csv(file, chunksize=chunksize):
        chunk.columns = chunk.columns.str.strip().str.lower()
        phone_columns = [col for col in chunk.columns if col.startswith('phone') and not col.startswith('phone type')]
        type_columns = [col for col in chunk.columns if col.startswith('phone type')]
        email_columns = [col for col in chunk.columns if col.startswith('email')]

        processed_data.extend(process_chunk(chunk, phone_columns, type_columns, email_columns))
    
    return pd.DataFrame(processed_data)

def main():
    st.title("Leads CSV to SMS Contacts Converter")

    url_input = st.text_input("Enter Google Sheets URL:")
    uploaded_file = st.file_uploader("Or upload your leads CSV file", type=["csv"])

    if url_input:
        raw_data = fetch_csv_from_url(url_input)
        if raw_data is not None:
            st.subheader("Raw Leads Data from URL")
            st.write(raw_data)

            processed_data = process_large_file(io.StringIO(raw_data.to_csv(index=False)))
            if not processed_data.empty:
                csv_buffer = io.StringIO()
                processed_data.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="Download Processed SMS Contacts",
                    data=csv_buffer.getvalue(),
                    file_name="processed_leads.csv",
                    mime='text/csv'
                )
            else:
                st.error("Processed data is empty.")

    elif uploaded_file is not None:
        try:
            processed_data = process_large_file(uploaded_file)
            if not processed_data.empty:
                csv_buffer = io.StringIO()
                processed_data.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="Download Processed SMS Contacts",
                    data=csv_buffer.getvalue(),
                    file_name="processed_leads.csv",
                    mime='text/csv'
                )
            else:
                st.error("Processed data is empty.")
        except Exception as e:
            st.error(f"An error occurred while processing the file: {e}")

if __name__ == "__main__":
    main()
