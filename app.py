import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import streamlit as st
import base64
from plotly.offline import iplot
import seaborn as sns
import math
import plotly.express as px
import plotly.express as px
import networkx as nx
from io import BytesIO

st.set_page_config(page_title="Final Project", page_icon=":bar_chart:", layout="wide", initial_sidebar_state='collapsed')

matches  = pd.read_csv("data/WorldCupMatches.csv")
players  = pd.read_csv("data/WorldCupPlayers.csv")
cups     = pd.read_csv("data/WorldCups.csv")

home_goals = matches.groupby('Home Team Name')['Home Team Goals'].sum()
away_goals = matches.groupby('Away Team Name')['Away Team Goals'].sum()
total_goals_per_country = home_goals.add(away_goals, fill_value=0)

total_goals_by_year = cups[['Year', 'GoalsScored']].set_index('Year')['GoalsScored']

###### DATA CLEANING ##########

def clean_data(players, matches, world_cup):
    # Drop rows with missing 'Year' in matches
    matches.dropna(subset=['Year'], inplace=True)

    # Clean 'Home Team Name' in matches
    names = matches[matches['Home Team Name'].str.contains('rn">')]['Home Team Name'].value_counts()
    wrong = list(names.index)
    correct = [name.split('>')[1] for name in wrong]
    old_name = ['Germany FR', 'Maracan� - Est�dio Jornalista M�rio Filho', 'Estadio do Maracana']
    new_name = ['Germany', 'Maracan Stadium', 'Maracan Stadium']
    wrong = wrong + old_name
    correct = correct + new_name

    for index, wr in enumerate(wrong):
        matches = matches.replace(wrong[index], correct[index])

    # Clean 'Winner', 'Runners-Up', and 'Third' in world_cup
    names_to_clean = ['Winner', 'Runners-Up', 'Third']
    for col in names_to_clean:
        for index, wr in enumerate(wrong):
            world_cup = world_cup.replace(wrong[index], correct[index])

    return players, matches, world_cup

players, matches, cups = clean_data(players, matches, cups)

######### CSS STyling #########
def get_base64_of_image(path):
    with open(path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return encoded_string

def add_bg_from_base64(base64_string):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{base64_string}");
            background-size: cover;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def set_title_color():
    st.markdown(
        """
        <style>
        .stApp h1 {
            color: white;
            font-weight: bold;

        }
        </style>
        """,
        unsafe_allow_html=True
    )

def add_fade_effect_only():
    st.markdown(
        """
        <style>
        .stApp::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            bottom: 0;
            left: 0;
            background-color: rgba(0, 0, 0, 0.5); /* Semi-transparent overlay */
            z-index: -1;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    
#### Functions of the vis ####

########1#########

def generate_goals_per_country_plot(matches_data):
    home = matches_data[['Home Team Name', 'Home Team Goals']].dropna()
    away = matches_data[['Away Team Name', 'Away Team Goals']].dropna()
    home.columns = ['Countries', 'Goals']
    away.columns = home.columns

    goals = pd.concat([home, away], ignore_index=True)
    goals = goals.groupby('Countries').sum()
    goals = goals.sort_values(by='Goals', ascending=False)

    fig = px.bar(
        goals[:20],
        x=goals.index[:20],
        y='Goals',
        labels={'Goals': 'Number of Goals'},
        title='Total Goals Scored by Country',
    )

    fig.update_layout(xaxis_title='Country Names', yaxis_title='Goals')

    return fig


def plot_total_goals_by_year(data):
    df = pd.DataFrame(list(data.items()), columns=['Year', 'Goals'])
    
    # Define a custom color scale from light blue to dark blue
    color_scale = [[0, 'lightblue'], [1, 'darkblue']]
    
    fig = px.scatter(
        df,
        x='Year',
        y='Goals',
        size='Goals',
        color='Goals',
        size_max=60,
        title='Total Goals Scored by Year',
        color_continuous_scale=color_scale  # Apply the custom color scale
    )
    
    return fig


def generate_top5_teams_goals_plot(matches_data):
    home = matches_data.groupby(['Year', 'Home Team Name'])['Home Team Goals'].sum()
    away = matches_data.groupby(['Year', 'Away Team Name'])['Away Team Goals'].sum()
    goals = pd.concat([home, away], axis=1)
    goals.fillna(0, inplace=True)
    goals['Goals'] = goals['Home Team Goals'] + goals['Away Team Goals']
    goals = goals.drop(labels=['Home Team Goals', 'Away Team Goals'], axis=1)
    goals = goals.reset_index()
    goals.columns = ['Year', 'Country', 'Goals']
    goals = goals.sort_values(by=['Year', 'Goals'], ascending=[True, False])
    top5 = goals.groupby('Year').head()

    data = []
    for team in top5['Country'].drop_duplicates().values:
        year = top5[top5['Country'] == team]['Year']
        goal = top5[top5['Country'] == team]['Goals']

        data.append(go.Bar(x=year, y=goal, name=team))

    layout = go.Layout(barmode='stack', title='Top 5 Teams with Most Goals every World Cup', showlegend=False)

    fig = go.Figure(data=data, layout=layout)
    
    return fig

########2#########
cups['Attendance'] = pd.to_numeric(cups['Attendance'].str.replace('.', ''), errors='coerce')

def plot_attendance_per_match_over_years(world_cup_data):
    # Ensure 'Attendance' is a numeric column

    # Calculate the ratio of Attendance to Matches Played
    world_cup_data['Attendance per Match'] = world_cup_data['Attendance'] / world_cup_data['MatchesPlayed']

    # Create the plot
    fig = px.line(
        world_cup_data, 
        x='Year', 
        y='Attendance per Match', 
        title='Average Attendance per Match Over the Years',
        labels={'Attendance per Match': 'Average Attendance per Match'},
        markers=True
    )

    fig.update_traces(line=dict(color='green'))
    fig.update_layout(xaxis_title='Year', yaxis_title='Average Attendance per Match')

    return fig

def generate_qualified_teams_per_year_plot(world_cup_data):
    fig = px.bar_polar(
        world_cup_data,
        r='QualifiedTeams',
        theta='Year',  # This will place the years on the circumference
        color="QualifiedTeams",
        template="plotly_dark",
        color_discrete_sequence=px.colors.sequential.Plasma_r,
        title='Qualified Teams Over the Years',
    )
    
    # Update layout to adjust theta axis for categorical data (years)
    fig.update_layout(
        polar_angularaxis=dict(
            type='category',  # Specify the axis type as category
            tickvals=world_cup_data['Year'],  # Set the tick values to the years
            ticktext=world_cup_data['Year']  # Set the tick text to the years
        )
    )

    return fig


def plot_interactions(year, color, matches):
    df = matches[matches["Year"] == year][["Home Team Name", "Away Team Name"]]
    G = nx.from_pandas_edgelist(df, "Home Team Name", "Away Team Name")
    
    # Set up a plot with the specified size
    plt.figure(figsize=(10, 9), facecolor='white')  # Set the background to white
    
    # Set the axes background color
    ax = plt.gca()
    ax.set_facecolor('white')
    
    # Draw the graph
    pos = nx.kamada_kawai_layout(G)
    nx.draw_networkx_nodes(G, pos, node_size=2500, node_color=color, node_shape="h")
    nx.draw_networkx_edges(G, pos, edge_color="k", width=2)
    nx.draw_networkx_labels(G, pos, font_size=13, font_color="k")
    
    # Title for the plot
    plt.title("Interaction between teams: " + str(year), fontsize=9, color="k")
    
    # Save the current figure to a bytes buffer
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor=ax.get_facecolor())
    plt.close()  # Close the figure to prevent display in the notebook/output
    buf.seek(0)
    
    # Use st.image to display the image from the bytes buffer
    st.image(buf, caption=f"Team Interactions in {year}")

# Example usage in Streamlit
# plot_interactions(1990, 'blue', matches)  # Replace 'matches' with your DataFrame

########3#########

def generate_top_attendance_matches_plot(matches_data):
    top10 = matches_data.sort_values(by='Attendance', ascending=False)[:10]
    top10['vs'] = top10['Home Team Name'] + " vs " + top10['Away Team Name']

    fig = px.bar(
        top10,
        y='vs',
        x='Attendance',
        orientation='h',
        title='Matches with the Highest Number of Attendance',
        labels={'Attendance': 'Attendance'},
    )

    fig.update_layout(
        yaxis=dict(title='Match Teams'),
        xaxis=dict(title='Attendance'),
    )

    # Add annotations for Stadium and Date inside the bars
    for i, (stadium, date, attendance) in enumerate(zip(top10['Stadium'], top10['Datetime'], top10['Attendance'])):
        # Extract only day, month, and year from the datetime
        date_str = pd.to_datetime(date).strftime('%d %b %Y')
        
        fig.add_annotation(
            x=attendance,
            y=i,
            text=f"Stadium: {stadium}, Date: {date_str}",
            font=dict(size=12, color='white'),
            showarrow=False,
            xanchor='right',  # Set anchor to the right for text inside the bars
            yanchor='auto',   # Align text to the center of the bar
            xshift=-50,         # Adjust xshift to control the position of the text
        )

    # Reverse the order of bars to have the max attendance at the top
    # fig.update_yaxes(categoryorder='total ascending')

    return fig

def plot_podium_count(world_cup_data):
    gold = world_cup_data["Winner"]
    silver = world_cup_data["Runners-Up"]
    bronze = world_cup_data["Third"]

    gold_count = pd.DataFrame.from_dict(gold.value_counts())
    silver_count = pd.DataFrame.from_dict(silver.value_counts())
    bronze_count = pd.DataFrame.from_dict(bronze.value_counts())

    podium_count = gold_count.join(silver_count, how='outer', lsuffix='_gold', rsuffix='_silver').join(bronze_count, how='outer', rsuffix='_bronze')
    podium_count = podium_count.fillna(0)
    podium_count.columns = ['WINNER', 'SECOND', 'THIRD']
    podium_count = podium_count.astype('int64')
    podium_count = podium_count.sort_values(by=['WINNER', 'SECOND', 'THIRD'], ascending=False)

    fig = px.bar(
        podium_count,
        y=['WINNER', 'SECOND', 'THIRD'],
        color_discrete_map={'WINNER': 'gold', 'SECOND': 'silver', 'THIRD': 'brown'},
        labels={'value': 'Number of Podiums'},
        title='Number of Podiums by Country',
    )

    fig.update_layout(
        xaxis=dict(title='Countries'),
        yaxis=dict(title='Podium Count'),
        barmode='stack',  # Stack bars on top of each other
    )

    return fig

def plot_goals_by_year(matches):
    # Ensure 'Year', 'Home Team Goals', and 'Away Team Goals' are in the correct format
    matches['Year'] = pd.to_numeric(matches['Year'], errors='coerce')
    matches['Home Team Goals'] = pd.to_numeric(matches['Home Team Goals'], errors='coerce')
    matches['Away Team Goals'] = pd.to_numeric(matches['Away Team Goals'], errors='coerce')

    # Create DataFrames for home and away goals
    gh = matches[["Year", "Home Team Goals"]].copy()
    gh.columns = ["year", "goals"]
    gh["type"] = "Home Team Goals"

    ga = matches[["Year", "Away Team Goals"]].copy()
    ga.columns = ["year", "goals"]
    ga["type"] = "Away Team Goals"

    # Concatenate and rename columns
    gls = pd.concat([gh, ga], axis=0)

    # Define a color map for the types
    color_map = {"Home Team Goals": "cyan", "Away Team Goals": "red"}

    # Create the violin plot with custom colors
    fig = px.violin(gls, x="year", y="goals", color="type", 
                    violinmode='overlay', 
                    color_discrete_map=color_map)

    # Update the y-axis to start from 0
    fig.update_yaxes(range=[0, gls['goals'].max()])

    fig.update_layout(title='Home and Away Goals by Year')

    return fig




    # Assuming your matches_data DataFrame has columns 'Year', 'Home Team Name', 'Away Team Name', 'Home Team Goals', 'Away Team Goals'

    # Create a new DataFrame to store the total goals scored by each country in each edition
    total_goals_data_home = matches_data.groupby(['Year', 'Home Team Name'])['Home Team Goals'].sum().reset_index()
    total_goals_data_away = matches_data.groupby(['Year', 'Away Team Name'])['Away Team Goals'].sum().reset_index()

    # Merge the total_goals_data for home and away teams
    total_goals_data = pd.concat([total_goals_data_home, total_goals_data_away], ignore_index=True)

    # Find the country with the maximum total goals in each year
    max_goals_data = total_goals_data.groupby('Year')['Home Team Goals'].max().reset_index()

    # Merge the max_goals_data with matches_data to get the Winner Goals
    matches_data = pd.merge(matches_data, max_goals_data, how='left', left_on=['Year', 'Home Team Name'], right_on=['Year', 'Home Team Name'], suffixes=('_match', '_max'))

    # Create a new column 'Winner Goals' based on the maximum goals
    matches_data['Winner Goals'] = matches_data.apply(lambda row: row['Home Team Goals_max'] if row['Home Team Goals_match'] > row['Away Team Goals_match'] else row['Away Team Goals_max'], axis=1)

    # Plotting
    fig = px.bar(matches_data, x='Year', y=['Winner Goals'],
                 labels={'value': 'Number of Goals'},
                 title='Maximum Goals Scored by Any Team and Number of Goals by Winning Team for Each Edition of World Cup')
    
    return fig

############ Streamlit UI ##########

image_path = 'image1.jpeg'  

st.title("From Kick off to Glory : FIFA Worldcup")

analysis_type = st.selectbox("Choose Analysis Type", ["Goal Analysis", "Attendance and Participation Analysis", "Cup Analysis"])

if analysis_type == "Goal Analysis":
    col1, col2, col3 = st.columns(3)
   
    with col1:
        # Cup Winning Count
        st.subheader("Goal Analysis")
        # st.write("Goals vs Countries")
        bar_fig = generate_goals_per_country_plot(matches)
        st.plotly_chart(bar_fig)

    with col2:
        # Total Goals Scored by Year
        st.subheader("")
        st.subheader("")
        # st.write("Total Goals Scored by Year")
        bubble_fig = plot_total_goals_by_year(total_goals_by_year)
        st.plotly_chart(bubble_fig)
    with col3:
        # Cup Winning Count
        st.subheader("")
        st.subheader("")
        # st.write("Goals vs Countries")
        bar_fig = generate_top5_teams_goals_plot(matches)
        st.plotly_chart(bar_fig)
    

if analysis_type == "Attendance and Participation Analysis":
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("")
        st.subheader("")
        st.subheader("Attendance and Participation Analysis")
        attendance_fig = plot_attendance_per_match_over_years(cups)
        st.plotly_chart(attendance_fig)
    with col2:
        st.subheader("")
        st.subheader("")
        st.write("")
        st.subheader("")
        teams_qualified_fig = generate_qualified_teams_per_year_plot(cups)
        st.plotly_chart(teams_qualified_fig)
    with col3:
        st.subheader("")
        st.subheader("")
        st.write("")
        st.subheader("")
        st.subheader("Team Interaction Analysis")
        # Network graph of team interactions for a selected year
        year_to_analyze = st.selectbox("Select a Year for Interaction Analysis", matches['Year'].unique(), key='year_select')
        color_to_use = "#ffcc00"  # A default color for the nodes, can be made dynamic with color picker
        if st.button("Show Interactions", key='interactions_btn'):
            plot_interactions(year_to_analyze, color_to_use, matches)

if analysis_type == "Cup Analysis":
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("")
        st.subheader("")
        st.subheader("Cup Analysis")
        top_attendance_fig = generate_top_attendance_matches_plot(matches)
        st.plotly_chart(top_attendance_fig)
    with col2:
        st.subheader("")
        st.subheader("")
        podium_count_fig = plot_podium_count(cups)
        st.plotly_chart(podium_count_fig)
    with col3:
        st.subheader("")
        st.subheader("")
        goals_comparison_fig = plot_goals_by_year(matches)
        st.plotly_chart(goals_comparison_fig)

