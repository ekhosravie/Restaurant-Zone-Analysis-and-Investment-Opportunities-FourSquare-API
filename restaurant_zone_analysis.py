# Step 1: Install necessary libraries
# %pip install plotly requests pandas scikit-learn

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
from sklearn.cluster import KMeans

# Step 2: Define constants
API_URL = "https://api.foursquare.com/v3/places/search"
API_KEY = "secret"  # Replace with your API key

HEADERS = {
    "Accept": "application/json",
    "Authorization": API_KEY,
}

ZONES = [
    "Bukit Bintang", "KL Sentral", "Petaling Street", "Shah Alam",
    "Petaling Jaya", "Puchong", "Batu Caves", "Kepong", "Klang", 
    "Seputeh", "Kuang", "Ampang", "Seputeh", "Wangsa Maju", 
    "Selayang", "Sungai Buloh", "Subang Jaya", "Kapar", "Mont Kiara"
]
QUERY = "restaurant"
LIMIT = 50

# Step 3: Fetch data for each zone
all_zone_data = []

for zone in ZONES:
    params = {
        "query": QUERY,
        "near": zone,
        "limit": LIMIT,
    }
    response = requests.get(API_URL, headers=HEADERS, params=params)
    if response.status_code == 200:
        data = response.json().get("results", [])
        for item in data:
            all_zone_data.append({
                "zone": zone,
                "name": item.get("name"),
                "latitude": item["geocodes"]["main"]["latitude"],
                "longitude": item["geocodes"]["main"]["longitude"],
                "category": item["categories"][0]["name"] if item.get("categories") else "Unknown",
            })
    else:
        print(f"Error fetching data for {zone}: {response.status_code}, {response.text}")

# Step 4: Create a DataFrame
df = pd.DataFrame(all_zone_data)

# Step 5: KMeans clustering based on restaurant categories
category_kmeans = KMeans(n_clusters=5, random_state=42)  # Adjust n_clusters as needed

# Assign a category cluster ID
df['category_cluster'] = category_kmeans.fit_predict(df[['category']].apply(lambda x: pd.factorize(x)[0]))


# Step 6: Enhanced scatter map visualization
df['cluster_info'] = df.apply(lambda row: f"Cluster: {row['category_cluster']}<br>Category: {row['category']}", axis=1)

fig = px.scatter_mapbox(
    df,
    lat="latitude",
    lon="longitude",
    color="category_cluster",
    hover_name="name",
    hover_data=["zone", "category", "cluster_info"],
    title="K-Means Clustering of Restaurants by Category",
    zoom=10,
    height=600,
)

fig.update_layout(
    mapbox_style="carto-positron",
    legend_title=dict(text="Restaurant Category Clusters"),
    margin=dict(l=10, r=10, t=40, b=10),
)
fig.show()

# Step 7: Generate cluster summary
cluster_summary = []

for cluster_id in sorted(df['category_cluster'].unique()):
    cluster_size = len(df[df['category_cluster'] == cluster_id])
    common_categories = df[df['category_cluster'] == cluster_id]['category'].value_counts()
    top_categories = ", ".join([f"{category} ({count})" for category, count in common_categories.items()])
    
    cluster_summary.append({
        "Cluster ID": cluster_id,
        "Total Restaurants": cluster_size,
        "Top Categories": top_categories
    })

# Convert summary to DataFrame
cluster_summary_df = pd.DataFrame(cluster_summary)

# Cluster summary bar chart
cluster_summary_df['Cluster ID'] = cluster_summary_df['Cluster ID'].astype(str)

bar_chart = px.bar(
    cluster_summary_df,
    x="Cluster ID",
    y="Total Restaurants",
    text="Top Categories",
    title="Restaurant Distribution Across Clusters",
    labels={"Total Restaurants": "Number of Restaurants", "Cluster ID": "Cluster"},
    color="Cluster ID",
    color_discrete_sequence=px.colors.qualitative.Set2,
    hover_data={"Top Categories": True},
)

bar_chart.update_traces(texttemplate='%{y}', textposition='outside')
bar_chart.update_layout(showlegend=False, height=500)
bar_chart.show()

# Step 8: Create a heatmap for category percentages
pivot_table = (
    df.groupby(['zone', 'category'])
    .size()
    .groupby(level=0)
    .apply(lambda x: 100 * x / float(x.sum()))
    .unstack(fill_value=0)
)

heatmap_fig = px.imshow(
    pivot_table.T,
    labels={"x": "Zone", "y": "Category", "color": "Percentage"},
    title="Restaurant Category Distribution by Zone",
    color_continuous_scale="Viridis",
    aspect="auto",
)

heatmap_fig.update_layout(height=700, margin=dict(l=10, r=10, t=40, b=10))
heatmap_fig.show()

# Step 9: Prepare cluster membership table
cluster_table_data = []

for cluster_id in df['category_cluster'].unique():
    members = df[df['category_cluster'] == cluster_id][['name', 'zone', 'category']].values
    for name, zone, category in members:
        cluster_table_data.append({
            "Cluster ID": cluster_id,
            "Restaurant Name": name,
            "Zone": zone,
            "Category": category,
        })

cluster_table_df = pd.DataFrame(cluster_table_data)

table_fig = go.Figure(
    data=[
        go.Table(
            header=dict(
                values=["Cluster ID", "Restaurant Name", "Zone", "Category"],
                fill_color="lightblue",
                align="left",
                font=dict(size=12, color="black"),
            ),
            cells=dict(
                values=[
                    cluster_table_df["Cluster ID"],
                    cluster_table_df["Restaurant Name"],
                    cluster_table_df["Zone"],
                    cluster_table_df["Category"],
                ],
                fill_color="lightgrey",
                align="left",
                font=dict(size=11, color="black"),
            ),
        )
    ]
)

table_fig.update_layout(title="Cluster Membership Table", height=700)
table_fig.show()

# Step 10: Cluster distribution across zones
cluster_distribution = (
    df.groupby(['zone', 'category_cluster']).size().reset_index(name='Count')
)
cluster_distribution['category_cluster'] = cluster_distribution['category_cluster'].astype(str)

stacked_bar = px.bar(
    cluster_distribution,
    x="zone",
    y="Count",
    color="category_cluster",
    title="Cluster Distribution Across Zones",
    labels={"zone": "Zone", "Count": "Number of Restaurants", "category_cluster": "Cluster"},
    color_discrete_sequence=px.colors.qualitative.Plotly,
)

stacked_bar.update_layout(height=600, xaxis_tickangle=-45)
stacked_bar.show()






# Step 11: Advanced investment recommendations by analyzing market competition and growth potential

# Calculate the restaurant count per zone for each category
zone_category_counts = df.groupby(['zone', 'category']).size().reset_index(name='Count')

# Normalize data by zone population density or expected restaurant saturation
zone_total_counts = df.groupby('zone')['category_cluster'].count().reset_index(name='Total_Restaurants')

# Merge total restaurant counts into the group to allow comparison
zone_category_counts = zone_category_counts.merge(zone_total_counts, on='zone', how='left')

# Calculate a "saturation rate" for each category in each zone
zone_category_counts['Saturation_Rate'] = (zone_category_counts['Count'] / zone_category_counts['Total_Restaurants']) * 100

# Debugging Step 1: Inspect the initial processed data
print("Zone-Category Counts with Saturation Rate:")
print(zone_category_counts.head(20))  # Display first 20 rows for insights

# Adjust threshold logic
investment_opportunity_threshold = 50  # Increased threshold for broader data inclusion

# Identify underrepresented categories in zones to highlight investment opportunities
investment_opportunities = zone_category_counts[zone_category_counts['Saturation_Rate'] < investment_opportunity_threshold]

# Debugging Step 2: Inspect filtered opportunities
print("Filtered Investment Opportunities:")
print(investment_opportunities.head(30))

# Sort and prioritize opportunities by competition rates and restaurant counts
investment_opportunities = investment_opportunities.sort_values(by='Saturation_Rate', ascending=True)

# Select only the top N opportunities for display (e.g., top 10 opportunities by low competition but high demand)
top_investment_zones = investment_opportunities.nlargest(10, 'Total_Restaurants')

# Debugging Step 3: Verify final recommended opportunities
print("Top Investment Opportunities:")
print(top_investment_zones)

# Prepare the table with the recommended investment opportunities
investment_recommendations_table = go.Figure(
    data=[
        go.Table(
            header=dict(
                values=["Zone", "Category", "Restaurants in Category", "Total Restaurants", "Saturation Rate (%)"],
                fill_color="lightblue",
                align="left",
                font=dict(size=12, color="black"),
            ),
            cells=dict(
                values=[
                    top_investment_zones['zone'],
                    top_investment_zones['category'],
                    top_investment_zones['Count'],
                    top_investment_zones['Total_Restaurants'],
                    top_investment_zones['Saturation_Rate'].round(2)
                ],
                fill_color="lightgrey",
                align="left",
                font=dict(size=11, color="black"),
            ),
        )
    ]
)

investment_recommendations_table.update_layout(
    title="Top Investment Opportunities by Zone and Restaurant Category",
    height=700
)

# Display recommendations
investment_recommendations_table.show()


