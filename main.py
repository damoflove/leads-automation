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

def extract_selected_phones(row, phone_columns, type_columns):
    selected_phones = []
    for phone_col, type_col in zip(phone_columns, type_columns):
        # Check that both columns exist and are not NaN
        if (
            phone_col in row.index and type_col in row.index and
            pd.notna(row[phone_col]) and pd.notna(row[type_col]) and
            str(row[type_col]).strip().lower() in ['wireless', 'voip']
        ):
            selected_phones.append(str(row[phone_col]).strip())
    return selected_phones

def extract_unique_emails(row, email_columns):
    emails = []
    for email_col in email_columns:
        if email_col in row.index and pd.notna(row[email_col]) and isinstance(row[email_col], str):
            emails.append(row[email_col].strip())
    return list(pd.unique(emails))

def process_leads_data(df):
    df.columns = df.columns.str.strip().str.lower()

    phone_columns = [col for col in df.columns if col.startswith('phone') and not col.startswith('phone type')]
    type_columns = [col for col in df.columns if col.startswith('phone type')]
    email_columns = [col for col in df.columns if col.startswith('email')]

    output_rows = []
    for _, row in df.iterrows():
        selected_phones = extract_selected_phones(row, phone_columns, type_columns)
        unique_emails = extract_unique_emails(row, email_columns)
        
        max_len = max(len(selected_phones), len(unique_emails), 1)  # Ensure at least one row is added

        for i in range(max_len):
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

    # Return a DataFrame of the processed data
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
                st.subheader("Processed SMS Contacts")
                st.write(processed_data)

                csv_buffer = io.StringIO()
                processed_data.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="Download Processed SMS Contacts",
                    data=csv_buffer.getvalue(),
                    file_name="processed_leads.csv",
                    mime='text/csv'
                )
            else:
                st.error("No data to process.")

    elif uploaded_file is not None:
        try:
            raw_data = pd.read_csv(uploaded_file)

            st.subheader("Raw Leads Data")
            st.write(raw_data)

            processed_data = process_leads_data(raw_data)
            if not processed_data.empty:
                st.subheader("Processed SMS Contacts")
                st.write(processed_data)

                csv_buffer = io.StringIO()
                processed_data.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="Download Processed SMS Contacts",
                    data=csv_buffer.getvalue(),
                    file_name="processed_leads.csv",
                    mime='text/csv'
                )
            else:
                st.error("No data to process.")
        except Exception as e:
            st.error(f"An error occurred while processing the file: {e}")

if __name__ == "__main__":
    main()
