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
    data = pd.read_csv(url)
    return data

# Cache processed data
@st.cache_data
def process_data(data):
    def parse_authors(row):
        authors_dict = ast.literal_eval(row['Full Authors'])
        authors = list(authors_dict.values())
        pairs = [(authors[i], authors[j], row['Title'], row['Year']) for i in range(len(authors)) for j in range(i+1, len(authors))]
        return pairs

    edges_data = defaultdict(lambda: {'count': 0, 'titles': [], 'years': [], 'authors': set()})
    author_collabs = defaultdict(int)
    
    for idx, row in data.iterrows():
        if pd.notnull(row['Full Authors']):
            pairs = parse_authors(row)
            for pair in pairs:
                edges_data[(pair[0], pair[1])]['count'] += 1
                edges_data[(pair[0], pair[1])]['titles'].append((pair[2], pair[3]))
                edges_data[(pair[0], pair[1])]['years'].append(pair[3])
                edges_data[(pair[0], pair[1])]['authors'].update([pair[0], pair[1]])
                author_collabs[pair[0]] += 1
                author_collabs[pair[1]] += 1
    
    edges_df = pd.DataFrame([(pair[0], pair[1], info['count'], info['titles'], info['years'], list(info['authors'])) for pair, info in edges_data.items()],
                            columns=['Author1', 'Author2', 'Weight', 'Titles', 'Years', 'Authors'])
    return edges_df, author_collabs

url = "https://raw.githubusercontent.com/22sgarg/PSB_Networks/main/full_author_results.csv"
data = load_data(url)
edges_df, author_collabs = process_data(data)

# Streamlit app
st.title('Evolving Co-authorship Network')
year = st.slider('Select Year', min_value=int(data['Year'].min()), max_value=int(data['Year'].max()), value=int(data['Year'].min()), step=1)

# Filter edges based on the selected year
def filter_edges_by_year(year, edges_df):
    filtered_edges = edges_df[edges_df['Years'].apply(lambda x: any(y <= year for y in x))]
    return filtered_edges

filtered_edges = filter_edges_by_year(year, edges_df)

# Create the network graph
net = Network(height='750px', width='100%', bgcolor='#FFFFFF', font_color='black', notebook=True)
opacity_step = 1 / (year - int(data['Year'].min()) + 1)
for idx, row in filtered_edges.iterrows():
    for y in row['Years']:
        if y <= year:
            opacity = 1 - (year - y) * opacity_step
            break
    node_size_1 = 5 + author_collabs[row['Author1']]
    node_size_2 = 5 + author_collabs[row['Author2']]
    net.add_node(row['Author1'], color='rgba(0, 0, 255, {opacity})'.format(opacity=opacity), size=node_size_1)
    net.add_node(row['Author2'], color='rgba(0, 0, 255, {opacity})'.format(opacity=opacity), size=node_size_2)
    title_str = f"Titles:<br>{'<br>'.join([f'{title} ({y})' for title, y in row['Titles']])}<br><br>Collaboration count: {row['Weight']}"
    net.add_edge(row['Author1'], row['Author2'], title=title_str, value=row['Weight'], color='rgba(0, 0, 255, {opacity})'.format(opacity=opacity))

net.show_buttons(filter_=['physics'])
net.show('network.html')

# Display the graph
HtmlFile = open('network.html', 'r', encoding='utf-8')
source_code = HtmlFile.read()
components.html(source_code, height=800)

# Sidebar dashboard
st.sidebar.title("Paper Metadata")
hover_data = st.sidebar.empty()
hover_data.markdown("Hover over a cluster or edge to see details here")

# Function to update sidebar with metadata
def update_sidebar(authors, titles):
    hover_data.markdown(f"**Authors:** {', '.join(authors)}\n\n**Titles and Years Published:**\n- " + '\n- '.join([f"{title} ({year})" for title, year in titles]))

# Placeholder for clicked edge data
if 'clicked_edge' not in st.session_state:
    st.session_state['clicked_edge'] = None

# Function to handle edge click
def edge_click(authors, titles):
    st.session_state['clicked_edge'] = (authors, titles)
    update_sidebar(authors, titles)

# Adding edge click event
for edge in net.edges:
    if edge['title']:
        authors = [edge['from'], edge['to']]
        titles = [(title.split('(')[0], int(title.split('(')[1].split(')')[0])) for title in edge['title'].split("<br>")[1:-2]]
        edge_click(authors, titles)

# Display clicked edge data
if st.session_state['clicked_edge']:
    authors, titles = st.session_state['clicked_edge']
    update_sidebar(authors, titles)
else:
    hover_data.markdown("Hover over a cluster or edge to see details here")
