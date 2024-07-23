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
            return pairs, authors_dict
        except Exception as e:
            st.error(f"Error parsing authors for row {row}: {e}")
            return [], {}

    edges_data = defaultdict(lambda: {'count': 0, 'titles': [], 'years': [], 'authors': set()})
    authors_data = defaultdict(lambda: {'titles': [], 'ids': []})
    
    for idx, row in data.iterrows():
        if pd.notnull(row['Full Authors']):
            pairs, authors_dict = parse_authors(row)
            for author, author_id in authors_dict.items():
                authors_data[author]['titles'].append(row['Title'])
                authors_data[author]['ids'].append(author_id)
            for pair in pairs:
                edges_data[(pair[0], pair[1])]['titles'].append((pair[2], pair[3]))
                edges_data[(pair[0], pair[1])]['years'].append(pair[3])
                edges_data[(pair[0], pair[1])]['authors'].update([pair[0], pair[1]])
    
    # Convert defaultdict to a regular dict for serialization
    edges_data = {k: dict(v) for k, v in edges_data.items()}
    authors_data = {k: dict(v) for k, v in authors_data.items()}
    return edges_data, authors_data

url = "https://raw.githubusercontent.com/22sgarg/PSB_Networks/main/full_author_results.csv"
data = load_data(url)
if data is not None:
    edges_data, authors_data = process_data(data)

    # Streamlit app
    st.title('Evolving Co-authorship Network')
    year = st.slider('Select Year', min_value=int(data['Year'].min()), max_value=int(data['Year'].max()), value=int(data['Year'].min()), step=1)

    # Filter edges based on the selected year
    def filter_edges_by_year(year, edges_data):
        filtered_edges = defaultdict(lambda: {'count': 0, 'titles': [], 'years': [], 'authors': set()})
        author_collabs = defaultdict(int)
        
        for (author1, author2), info in edges_data.items():
            recent_years = [y for y in info['years'] if y <= year]
            if recent_years:
                filtered_edges[(author1, author2)]['count'] = len(recent_years)
                filtered_edges[(author1, author2)]['titles'] = [(title, y) for title, y in info['titles'] if y <= year]
                filtered_edges[(author1, author2)]['years'] = recent_years
                filtered_edges[(author1, author2)]['authors'] = info['authors']
                author_collabs[author1] += len(recent_years)
                author_collabs[author2] += len(recent_years)
        
        return dict(filtered_edges), dict(author_collabs)

    filtered_edges, author_collabs = filter_edges_by_year(year, edges_data)

    # Create the network graph
    net = Network(height='750px', width='100%', bgcolor='#FFFFFF', font_color='black', notebook=True)
    opacity_step = 1 / (year - int(data['Year'].min()) + 1)
    for (author1, author2), info in filtered_edges.items():
        most_recent_year = max(info['years'])
        opacity = 1 - (year - most_recent_year) * opacity_step
        node_size_1 = 5 + author_collabs[author1]
        node_size_2 = 5 + author_collabs[author2]
        net.add_node(author1, color=f'rgba(0, 0, 255, {opacity})', size=node_size_1)
        net.add_node(author2, color=f'rgba(0, 0, 255, {opacity})', size=node_size_2)
        title_str = f"Collaboration count: {info['count']}"
        net.add_edge(author1, author2, title=title_str, value=info['count'], color=f'rgba(0, 0, 255, {opacity})')

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
    if 'clicked_node' not in st.session_state:
        st.session_state['clicked_node'] = None

    # Function to handle edge click
    def edge_click(authors, titles):
        st.session_state['clicked_edge'] = (authors, titles)
        st.session_state['clicked_node'] = None
        update_sidebar(authors, titles)

    # Function to handle node click
    def node_click(author):
        titles = authors_data[author]['titles']
        ids = authors_data[author]['ids']
        hover_data.markdown(f"**Author:** {author}\n\n**IDs:** {', '.join(ids)}\n\n**Titles:**\n- " + '\n- '.join(titles))

    # Adding edge click event
    for edge in net.edges:
        if edge['title']:
            authors = [edge['from'], edge['to']]
            titles = []
            for title in edge['title'].split("<br>")[1:-2]:
                try:
                    parsed_title = title.split('(')
                    year = int(parsed_title[1].split(')')[0])
                    titles.append((parsed_title[0].strip(), year))
                except (IndexError, ValueError) as e:
                    st.error(f"Error parsing title: {title}, error: {e}")
            edge_click(authors, titles)

    # Adding node click event
    for node in net.nodes:
        node_click(node['id'])

    # Display clicked edge data
    if st.session_state['clicked_edge']:
        authors, titles = st.session_state['clicked_edge']
        update_sidebar(authors, titles)
    elif st.session_state['clicked_node']:
        node_click(st.session_state['clicked_node'])
    else:
        hover_data.markdown("Hover over a cluster or edge to see details here")
else:
    st.error("Failed to load data.")
