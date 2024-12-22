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
    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()

    # Identify relevant columns
    phone_columns = [col for col in df.columns if col.startswith('phone') and not col.startswith('phone type')]
    type_columns = [col for col in df.columns if col.startswith('phone type')]
    email_columns = [col for col in df.columns if col.startswith('email')]

    # Function to extract wireless/VOIP phone numbers
    def extract_selected_phones(row):
        selected_phones = []
        for phone_col, type_col in zip(phone_columns, type_columns):
            # Ensure valid columns exist and check for specific conditions
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

    # Function to extract unique emails
    def extract_unique_emails(row):
        emails = [
            row[col].strip()
            for col in email_columns
            if col in row.index and pd.notna(row[col]) and isinstance(row[col], str)
        ]
        return list(pd.unique(emails))

    # Apply extraction functions
    df['selected_phones'] = df.apply(extract_selected_phones, axis=1)
    df['unique_emails'] = df.apply(extract_unique_emails, axis=1)

    # Create output rows
    output_rows = []
    for _, row in df.iterrows():
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

    # Return processed DataFrame
    if not output_rows:
        return pd.DataFrame(columns=['First Name', 'Last Name', 'Email', 'Mobile Phone', 'Address', 'City', 'State', 'Zip Code'])

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
            if not processed_data.empty:
                csv_buffer = io.StringIO()
                processed_data.to_csv(csv_buffer, index=False)
                csv_bytes = csv_buffer.getvalue().encode('utf-8')

                st.download_button(
                    label="Download Processed SMS Contacts",
                    data=csv_bytes,
                    file_name="processed_leads.csv",
                    mime='text/csv'
                )
            else:
                st.error("Processed data is empty.")
    elif uploaded_file is not None:
        try:
            raw_data = pd.read_csv(uploaded_file)

            st.subheader("Raw Leads Data")
            st.write(raw_data)

            processed_data = process_leads_data(raw_data)
            if not processed_data.empty:
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
            else:
                st.error("Processed data is empty.")
        except Exception as e:
            st.error(f"An error occurred while processing the file: {e}")

if __name__ == "__main__":
    main()
