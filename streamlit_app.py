import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
import ast

# Load the data
@st.cache
def load_data():
    url = "https://raw.githubusercontent.com/yourusername/your-repo-name/main/full_author_results.csv"
    return pd.read_csv(url)

data = load_data()

# Parse the Full Authors column and create co-authorship pairs
def parse_authors(row):
    authors_dict = ast.literal_eval(row['Full Authors'])
    authors = list(authors_dict.values())
    pairs = [(authors[i], authors[j]) for i in range(len(authors)) for j in range(i+1, len(authors))]
    return pairs

# Function to filter edges based on the selected year
def filter_edges_by_year(year, data):
    filtered_data = data[data['Year'] <= year]
    filtered_edges = defaultdict(int)
    for idx, row in filtered_data.iterrows():
        if pd.notnull(row['Full Authors']):
            pairs = parse_authors(row)
            for pair in pairs:
                filtered_edges[pair] += 1
    edges_df = pd.DataFrame([(*pair, weight) for pair, weight in filtered_edges.items()], columns=['Author1', 'Author2', 'Weight'])
    return edges_df

# Streamlit app
st.title('Evolving Co-authorship Network')
year = st.slider('Select Year', min_value=int(data['Year'].min()), max_value=int(data['Year'].max()), value=int(data['Year'].min()), step=1)

# Filter edges based on the selected year
filtered_edges = filter_edges_by_year(year, data)

# Create the network graph
G = nx.Graph()
for idx, row in filtered_edges.iterrows():
    G.add_edge(row['Author1'], row['Author2'], weight=row['Weight'])

# Draw the graph
pos = nx.spring_layout(G)
weights = [G[u][v]['weight'] for u, v in G.edges()]
nx.draw(G, pos, with_labels=True, node_size=500, node_color="skyblue", font_size=10, font_weight="bold", edge_color=weights, edge_cmap=plt.cm.Blues, width=weights)
plt.title(f'Co-authorship Network up to {year}')
st.pyplot(plt)
