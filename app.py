import streamlit as st
import pandas as pd

# Load and clean data
@st.cache_data
def load_data():
    matches = pd.read_csv("data/matches.csv")
    deliveries = pd.read_csv("data/deliveries.csv")
    
    team_name_mapping = {
        'Royal Challengers Bengaluru': 'Royal Challengers Bangalore',
        'Delhi Daredevils': 'Delhi Capitals',
        'Kings XI Punjab': 'Punjab Kings',
        'Rising Pune Supergiants': 'Rising Pune Supergiant',
    }
    
    for col in ['team1', 'team2', 'winner', 'toss_winner']:
        matches[col] = matches[col].replace(team_name_mapping)

    return matches, deliveries

# Helper Functions
def calculate_toss_win_percentage(matches):
    teams = set(matches['team1']).union(set(matches['team2']))
    team_toss_win_perc = {}

    for team in teams:
        toss_wins = matches[matches['toss_winner'] == team]
        toss_and_match_win = toss_wins[toss_wins['winner'] == team]
        if len(toss_wins) > 0:
            perc = len(toss_and_match_win) / len(toss_wins) * 100
            team_toss_win_perc[team] = round(perc, 2)

    sorted_teams = sorted(team_toss_win_perc.items(), key=lambda x: x[1], reverse=True)
    return pd.DataFrame(sorted_teams, columns=["Team", "Toss-to-Win %"]), team_toss_win_perc

def calculate_overall_toss_win(matches):
    overall_toss_wins = matches[matches['toss_winner'] == matches['winner']].shape[0]
    return round((overall_toss_wins / matches.shape[0]) * 100, 2)

def calculate_win_percentage(matches):
    team_wins = matches['winner'].value_counts()
    match_played = matches['team1'].value_counts() + matches['team2'].value_counts()
    return (team_wins / match_played * 100).sort_values(ascending=False)

def calculate_dominant_wins(matches):
    def adj_margin(row):
        if row['result'] == 'runs':
            return row['result_margin']
        else:
            return row['result_margin'] * 10

    matches['adj_margin'] = matches.apply(adj_margin, axis=1)
    dominant_wins = matches.groupby('winner')['adj_margin'].mean()
    most_dominant_team = dominant_wins.idxmax()
    return dominant_wins.sort_values(ascending=False), most_dominant_team

def calculate_top_motm(matches):
    motm_per_season = matches.groupby(['season', 'player_of_match']).size().reset_index(name='count')
    top_motm_per_season = motm_per_season.loc[motm_per_season.groupby('season')['count'].idxmax()]
    return top_motm_per_season

def calculate_top_batsman(deliveries, matches):
    merged_df = deliveries.merge(matches[['id', 'season']], left_on='match_id', right_on='id')
    batsman_runs = merged_df.groupby(['season', 'batter'])['batsman_runs'].sum().reset_index()
    
    legal_deliveries = merged_df[merged_df['extras_type'] != 'wides']
    balls_faced = legal_deliveries.groupby(['season', 'batter']).size().reset_index(name='balls_faced')
    batsman_stats = batsman_runs.merge(balls_faced, on=['season', 'batter'])
    top_batsman_stats = batsman_stats.sort_values(['season', 'batsman_runs'], ascending=[True, False]).drop_duplicates('season')
    top_batsman_stats['strike_rate'] = (top_batsman_stats['batsman_runs'] / top_batsman_stats['balls_faced']) * 100
    return top_batsman_stats

def calculate_top_wicket_taker(deliveries, matches):
    merged_df = deliveries.merge(matches[['id', 'season']], left_on='match_id', right_on='id')
    wickets_df = merged_df[(merged_df['is_wicket'] == 1) & (merged_df['dismissal_kind'] != 'run_out')]
    wickets_taken = wickets_df.groupby(['season', 'bowler']).size().reset_index(name='total_wickets')
    top_wicket_taker = wickets_taken.sort_values(['season', 'total_wickets'], ascending=[True, False]).drop_duplicates('season')
    return top_wicket_taker

def calculate_top_catch_taker(deliveries, matches):
    merged_df = deliveries.merge(matches[['id', 'season']], left_on='match_id', right_on='id')
    catch_df = merged_df[merged_df['dismissal_kind'] == 'caught']
    catch_taken = catch_df.groupby(['season', 'fielder']).size().reset_index(name='total_catches')
    top_catch_taker = catch_taken.sort_values(['season', 'total_catches'], ascending=[True, False]).drop_duplicates('season')
    return top_catch_taker

def team1():
    option = st.selectbox(
        'Select team 1',
        ('Rajasthan Royals', 'Pune Warriors', 'Mumbai Indians', 'Deccan Chargers', 'Gujarat Lions', 'Kolkata Knight Riders', 'Rising Pune Supergiant', 'Kochi Tuskers Kerala', 'Sunrisers Hyderabad', 'Royal Challengers Bangalore', 'Lucknow Super Giants', 'Delhi Capitals', 'Punjab Kings', 'Chennai Super Kings', 'Gujarat Titans'),
        key='team1_select'
    )
    return option

def team2():
    option = st.selectbox(
        'Select team 2',
        ('Rajasthan Royals', 'Pune Warriors', 'Mumbai Indians', 'Deccan Chargers', 'Gujarat Lions', 'Kolkata Knight Riders', 'Rising Pune Supergiant', 'Kochi Tuskers Kerala', 'Sunrisers Hyderabad', 'Royal Challengers Bangalore', 'Lucknow Super Giants', 'Delhi Capitals', 'Punjab Kings', 'Chennai Super Kings', 'Gujarat Titans'),
        key='team2_select'
    )
    return option

def calculate_head_to_head(matches, team1, team2):
    team1score = 0
    team2score = 0
    head_to_head = matches[(matches['team1'] == team1) & (matches['team2'] == team2) | (matches['team1'] == team2) & (matches['team2'] == team1)]
    for _, row in head_to_head.iterrows():
        if row['winner'] == team1:
            team1score += 1
        elif row['winner'] == team2:
            team2score += 1
    return team1score, team2score

# Main App
st.set_page_config(page_title="IPL Analysis Dashboard", layout="wide")
st.title("🏏 IPL Analysis Dashboard")

matches, deliveries = load_data()

# Sidebar navigation
options = [
    "Toss Win %",
    "Win %",
    "Dominant Wins",
    "Top MOTM Winners",
    "Top Batsmen",
    "Top Wicket Takers",
    "Top Catch Takers",
    "Head-to-Head"
]

choice = st.sidebar.selectbox("Select Analysis Section", options)

if choice == "Toss Win %":
    st.header(" Toss Win → Match Win %")
    df, _ = calculate_toss_win_percentage(matches)
    st.dataframe(df)

    overall = calculate_overall_toss_win(matches)
    st.metric(label="Overall Toss→Win %", value=f"{overall}%")

elif choice == "Win %":
    st.header(" Win Percentage of Each Team")
    st.dataframe(calculate_win_percentage(matches))

elif choice == "Dominant Wins":
    st.header(" Dominant Wins per Team")
    dominant_wins, most_dominant_team = calculate_dominant_wins(matches)
    st.dataframe(dominant_wins)
    st.write(f"Most dominant team: {most_dominant_team}")

elif choice == "Top MOTM Winners":
    st.header(" Top MOTM Winners per Season")
    st.dataframe(calculate_top_motm(matches))

elif choice == "Top Batsmen":
    st.header(" Top Batsmen and Their Strike Rates")
    st.dataframe(calculate_top_batsman(deliveries, matches))

elif choice == "Top Wicket Takers":
    st.header(" Top Wicket Takers per Season")
    st.dataframe(calculate_top_wicket_taker(deliveries, matches))

elif choice == "Top Catch Takers":
    st.header(" Top Catch Takers per Season")
    st.dataframe(calculate_top_catch_taker(deliveries, matches))

elif choice == "Head-to-Head":
    st.header(" Head-to-Head Stats")
    team1 = team1()
    team2 = team2()
    team1score, team2score = calculate_head_to_head(matches, team1, team2)
    st.write(f"{team1}: {team1score} | {team2}: {team2score}")
