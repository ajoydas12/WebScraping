import streamlit as st
from streamlit_tags import st_tags_sidebar
import pandas as pd
import json
from datetime import datetime
from scraper import fetch_html_selenium, save_raw_data, format_data, save_formatted_data, calculate_price, html_to_markdown_with_readability, create_dynamic_listing_model, create_listings_container_model

# Initialize Streamlit app
st.set_page_config(page_title="Universal Web Scraper", page_icon="🦑", layout="wide")
st.title("Universal Web Scraper 🦑")

# Sidebar components
st.sidebar.header("Settings ⚙️")
model_selection = st.sidebar.selectbox("Select Model", options=["gpt-4o-mini", "gpt-4o-2024-08-06"], index=0)

# URL input with validation
url_input = st.sidebar.text_input("Enter URL", placeholder="https://example.com")
if not url_input:
    st.sidebar.warning("Please enter a valid URL.")

# Tags input for fields to extract
tags = st.sidebar.empty()  # Create an empty placeholder in the sidebar
tags = st_tags_sidebar(
    label='Enter Fields to Extract:',
    text='Press enter to add a tag',
    value=[],  # Default values if any
    suggestions=[],  # You can still offer suggestions, or keep it empty for complete freedom
    maxtags=-1,  # Set to -1 for unlimited tags
    key='tags_input'
)

fields = tags

# Display token usage in a dedicated section
st.sidebar.markdown("---")
st.sidebar.subheader("Token Usage 💳")
input_tokens = output_tokens = total_cost = 0  # Default values

# Scraping function
def perform_scrape():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    raw_html = fetch_html_selenium(url_input)
    markdown = html_to_markdown_with_readability(raw_html)
    save_raw_data(markdown, timestamp)
    DynamicListingModel = create_dynamic_listing_model(fields)
    DynamicListingsContainer = create_listings_container_model(DynamicListingModel)
    formatted_data = format_data(markdown, DynamicListingsContainer)
    formatted_data_text = json.dumps(formatted_data.dict())
    input_tokens, output_tokens, total_cost = calculate_price(markdown, formatted_data_text, model=model_selection)
    df = save_formatted_data(formatted_data, timestamp)

    return df, formatted_data, markdown, input_tokens, output_tokens, total_cost, timestamp

# Handling scrape button
if 'perform_scrape' not in st.session_state:
    st.session_state['perform_scrape'] = False

# Button to trigger scraping
if st.sidebar.button("Start Scraping 🕸️"):
    if url_input:
        with st.spinner('Please wait... Scraping the data 🕵️‍♂️'):
            st.session_state['results'] = perform_scrape()
            st.session_state['perform_scrape'] = True
    else:
        st.sidebar.error("Please enter a valid URL before scraping!")

# Display results
if st.session_state.get('perform_scrape'):
    df, formatted_data, markdown, input_tokens, output_tokens, total_cost, timestamp = st.session_state['results']

    # Show data in tabs
    tab1, tab2, tab3 = st.tabs(["📊 Data", "📝 Markdown", "⚙️ Tokens"])

    with tab1:
        st.write("Scraped Data Preview:")
        st.dataframe(df)

    with tab2:
        st.write("Generated Markdown:")
        st.code(markdown)

    with tab3:
        st.metric("Input Tokens", input_tokens)
        st.metric("Output Tokens", output_tokens)
        st.metric("Total Cost ($)", f"${total_cost:.4f}")

    # Download buttons
    st.subheader("Download Results 💾")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button("Download JSON", data=json.dumps(formatted_data.dict(), indent=4), file_name=f"{timestamp}_data.json", mime='application/json')

    with col2:
        data_dict = formatted_data.dict() if hasattr(formatted_data, 'dict') else formatted_data
        first_key = next(iter(data_dict))
        main_data = data_dict[first_key]
        df = pd.DataFrame(main_data)
        st.download_button("Download CSV", data=df.to_csv(index=False), file_name=f"{timestamp}_data.csv", mime='text/csv')

    with col3:
        st.download_button("Download Markdown", data=markdown, file_name=f"{timestamp}_data.md", mime='text/markdown')

# Persistent UI components
if 'results' in st.session_state:
    df, formatted_data, markdown, input_tokens, output_tokens, total_cost, timestamp = st.session_state['results']
