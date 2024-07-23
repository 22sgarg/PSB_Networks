import streamlit as st
import pandas as pd
import networkx as nx
from collections import defaultdict
import ast
from pyvis.network import Network
import streamlit.components.v1 as components

# Load the data
@st.cache_data
def load_data(url):
    try:
        data = pd.read_csv(url)
        return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Process the data
@st.cache_data
def process_data(data):
    def parse_authors(row):
        try:
            authors_dict = ast.literal_eval(row['Full Authors'])
            authors = list(authors_dict.values())
            pairs = [(authors[i], authors[j], row['Title'], row['Year']) for i in range(len(authors)) for j in range(i+1, len(authors))]
            return pairs
        except Exception as e:
            st.error(f"Error parsing authors for row {row}: {e}")
            return []

    edges_data = defaultdict(lambda: {'count': 0, 'titles': [], 'years': [], 'authors': set()})
    
    for idx, row in data.iterrows():
        if pd.notnull(row['Full Authors']):
            pairs = parse_authors(row)
            for pair in pairs:
                edges_data[(pair[0], pair[1])]['titles'].append((pair[2], pair[3]))
                edges_data[(pair[0], pair[1])]['years'].append(pair[3])
                edges_data[(pair[0], pair[1])]['authors'].update([pair[0], pair[1]])
    
    # Convert defaultdict to a regular dict for serialization
    edges_data = {k: dict(v) for k, v in edges_data.items()}
    return edges_data

url = "https://raw.githubusercontent.com/22sgarg/PSB_Networks/main/full_author_results.csv"
data = load_data(url)
if data is not None:
    edges_data = process_data(data)

    # Streamlit app
    st.title('Evolving Co-authorship Network')
    year = st.slider('Select Year', min_value=int(data['Year'].min()), max_value=int(data['Year'].max()), value=int(data['Year'].min()), step=1)

    # Filter edges based on the selected year
    def filter_edges_by_year(year, edges_data):
        filtered_edges = defaultdict(lambda: {'count': 0, 'titles': [], 'years': [], 'authors': set()})
        
        for (author1, author2), info in edges_data.items():
            recent_years = [y for y in info['years'] if y <= year]
            if recent_years:
                filtered_edges[(author1, author2)]['count'] = len(recent_years)
                filtered_edges[(author1, author2)]['titles'] = [(title, y) for title, y in info['titles'] if y <= year]
                filtered_edges[(author1, author2)]['years'] = recent_years
                filtered_edges[(author1, author2)]['authors'] = info['authors']
        
        return dict(filtered_edges)

    filtered_edges = filter_edges_by_year(year, edges_data)

    # Create the network graph
    net = Network(height='750px', width='100%', bgcolor='#FFFFFF', font_color='black', notebook=True, directed=False)
    
    # Set hierarchical layout options
    net.set_options("""
    var options = {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "UD",  # UD = Top-Down
          "sortMethod": "hubsize"  # hubsize = Sort nodes based on the hub size
        }
      },
      "physics": {
        "enabled": false  # Disable physics for stable layout
      }
    }
    """)
    
    for (author1, author2), info in filtered_edges.items():
        net.add_node(author1, color='blue')
        net.add_node(author2, color='blue')
        title_str = f"Collaboration count: {info['count']}"
        net.add_edge(author1, author2, title=title_str, value=info['count'], color='blue')

    net.show('network.html')

    # Display the graph
    HtmlFile = open('network.html', 'r', encoding='utf-8')
    source_code = HtmlFile.read()
    components.html(source_code, height=800)
else:
    st.error("Failed to load data.")
