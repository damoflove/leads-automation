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

    # Identify phone and phone type columns
    phone_columns = [col for col in df.columns if col.startswith('phone') and not col.startswith('phone type')]
    type_columns = [col for col in df.columns if col.startswith('phone type')]
    email_columns = [col for col in df.columns if col.startswith('email')]

    # Extract Wireless and Void phone numbers only
    def extract_selected_phones(row):
        selected_phones = []
        for phone_col, type_col in zip(phone_columns, type_columns):
            phone = row.get(phone_col, None)
            phone_type = row.get(type_col, None)

            # Normalize phone type to lowercase for comparison
            if (
                phone is not None and
                phone_type is not None and
                str(phone_type).strip().lower() in ['wireless', 'void']
            ):
                selected_phones.append(str(phone).strip())  # Append phone number
        return selected_phones

    # Normalize email values
    df['unique_emails'] = df[email_columns].apply(lambda row: row.dropna().unique().tolist(), axis=1)
    df['selected_phones'] = df.apply(extract_selected_phones, axis=1)

    output_rows = []
    for _, row in df.iterrows():
        selected_phones = row['selected_phones']
        unique_emails = row['unique_emails']

        # Duplicate rows based on the number of phone numbers
        for i in range(len(selected_phones)):
            output_rows.append({
                'First Name': row.get('firstname', ""),
                'Last Name': row.get('lastname', ""),
                'Email': unique_emails[i] if i < len(unique_emails) else "",  # Leave empty if no email
                'Mobile Phone': selected_phones[i],
                'Address': row.get('propertyaddress', ""),
                'City': row.get('propertycity', ""),
                'State': row.get('propertystate', ""),
                'Zip Code': row.get('propertypostalcode', "")
            })

    # If no rows were added, return an empty DataFrame
    if not output_rows:
        return pd.DataFrame(columns=['First Name', 'Last Name', 'Email', 'Mobile Phone', 'Address', 'City', 'State', 'Zip Code'])

    output_df = pd.DataFrame(output_rows)
    return output_df

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
            raw_data = pd.read_csv(uploaded_file)

            st.subheader("Raw Leads Data")
            st.write(raw_data)

            processed_data = process_leads_data(raw_data)

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
