import streamlit as st
import pandas as pd
import networkx as nx
from collections import defaultdict
import ast
from pyvis.network import Network
import streamlit.components.v1 as components

# Load the data
@st.cache
def load_data(url):
    try:
        data = pd.read_csv(url)
        return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

url = "https://raw.githubusercontent.com/22sgarg/PSB_Networks/main/full_author_results.csv"
data = load_data(url)

if data is not None:
    # Parse the Full Authors column and create co-authorship pairs
    def parse_authors(row):
        authors_dict = ast.literal_eval(row['Full Authors'])
        authors = list(authors_dict.values())
        pairs = [(authors[i], authors[j], row['Title']) for i in range(len(authors)) for j in range(i+1, len(authors))]
        return pairs

    # Function to filter edges based on the selected year
    def filter_edges_by_year(year, data):
        filtered_data = data[data['Year'] <= year]
        filtered_edges = defaultdict(list)
        for idx, row in filtered_data.iterrows():
            if pd.notnull(row['Full Authors']):
                pairs = parse_authors(row)
                for pair in pairs:
                    filtered_edges[(pair[0], pair[1])].append(pair[2])
        edges_df = pd.DataFrame([(*pair, titles) for pair, titles in filtered_edges.items()], columns=['Author1', 'Author2', 'Titles'])
        return edges_df

    # Streamlit app
    st.title('Evolving Co-authorship Network')
    year = st.slider('Select Year', min_value=int(data['Year'].min()), max_value=int(data['Year'].max()), value=int(data['Year'].min()), step=1)

    # Filter edges based on the selected year
    filtered_edges = filter_edges_by_year(year, data)

    # Create the network graph
    net = Network(height='750px', width='100%', bgcolor='#222222', font_color='white', notebook=True)
    for idx, row in filtered_edges.iterrows():
        net.add_node(row['Author1'])
        net.add_node(row['Author2'])
        net.add_edge(row['Author1'], row['Author2'], title='<br>'.join(row['Titles']), value=len(row['Titles']))

    net.show_buttons(filter_=['physics'])
    net.show('network.html')

    # Display the graph
    HtmlFile = open('network.html', 'r', encoding='utf-8')
    source_code = HtmlFile.read()
    components.html(source_code, height=800)
else:
    st.error("Failed to load data.")
