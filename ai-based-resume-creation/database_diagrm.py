import matplotlib.pyplot as plt
import networkx as nx

# Define the schema as a graph
schema_graph = nx.DiGraph()

# Tables and their relationships
tables = {
    "Users": ["user_id (PK)", "username", "password_hash", "role", "created_at", "last_login"],
    "User_Info": ["user_info_id (PK)", "user_id (FK)", "full_name", "age", "email", "phone", "address", "summary", "years_experience", "created_at"],
    "Resumes": ["resume_id (PK)", "user_id (FK)", "file_pdf", "file_md", "template_id (FK)", "created_at", "updated_at"],
    "Experience": ["experience_id (PK)", "user_id (FK)", "job_title", "company", "start_date", "end_date", "description"],
    "Education": ["education_id (PK)", "user_id (FK)", "institution", "degree", "field_of_study", "start_year", "end_year", "grade"],
    "Skills": ["skill_id (PK)", "user_id (FK)", "skill_name", "proficiency"],
    "Job_Role_Content": ["job_role_id (PK)", "role_name", "content_md", "sample_summary", "tips"],
    "Resume_Templates": ["template_id (PK)", "name", "html_structure", "css_style", "preview_image"]
}

# Add nodes and edges
for table, columns in tables.items():
    schema_graph.add_node(table, label="\n".join([table] + columns))

# Add foreign key relationships
edges = [
    ("User_Info", "Users"),
    ("Resumes", "Users"),
    ("Resumes", "Resume_Templates"),
    ("Experience", "Users"),
    ("Education", "Users"),
    ("Skills", "Users")
]
schema_graph.add_edges_from(edges)

# Draw the graph
pos = nx.spring_layout(schema_graph, seed=42)
plt.figure(figsize=(18, 12))
nx.draw_networkx(schema_graph, pos, node_color='skyblue', node_size=6000, font_size=10, font_weight='bold', edge_color='gray')
labels = nx.get_node_attributes(schema_graph, 'label')
for node, (x, y) in pos.items():
    plt.text(x, y, labels[node], fontsize=9, ha='center', va='center', bbox=dict(facecolor='white', alpha=0.8))
plt.title("AI Resume Builder - Database Schema Diagram", fontsize=16)
plt.axis('off')
plt.show()
