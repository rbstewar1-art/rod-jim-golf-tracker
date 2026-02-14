import streamlit as st
import sqlite3
import pandas as pd

# Connect to DB
conn = sqlite3.connect('golf_matches.db')
cur = conn.cursor()

# Helper to calculate match summaries from hole data
def calculate_summaries(hole_df):
    hole_df['Hole Winner'] = hole_df.apply(lambda row: 'Rod' if row['Rod Score'] < row['Jim Score'] else 'Jim' if row['Jim Score'] < row['Rod Score'] else 'Tie', axis=1)
    rod_won_cum, jim_won_cum = [0], [0]
    match_status = ['All Square']
    for i in range(1, len(hole_df) + 1):
        prev_rod, prev_jim = rod_won_cum[-1], jim_won_cum[-1]
        winner = hole_df.iloc[i-1]['Hole Winner']
        rod_won_cum.append(prev_rod + 1 if winner == 'Rod' else prev_rod)
        jim_won_cum.append(prev_jim + 1 if winner == 'Jim' else prev_jim)
        diff = rod_won_cum[-1] - jim_won_cum[-1]
        if i == 18:
            status = f"{abs(diff)} Up ({'Rod' if diff > 0 else 'Jim'} wins the match)" if diff != 0 else "All Square"
        else:
            status = f"{abs(diff)} Up ({'Rod' if diff > 0 else 'Jim'})" if diff != 0 else "All Square"
        match_status.append(status)
    hole_df['Rod Won'] = rod_won_cum[1:]
    hole_df['Jim Won'] = jim_won_cum[1:]
    hole_df['Match Status'] = match_status[1:]
    
    rod_front_wins = hole_df.iloc[0:9]['Rod Won'].max()
    jim_front_wins = hole_df.iloc[0:9]['Jim Won'].max()
    front9_winner = f"Rod wins Front 9 by {rod_front_wins - jim_front_wins}" if rod_front_wins > jim_front_wins else f"Jim wins Front 9 by {jim_front_wins - rod_front_wins}" if jim_front_wins > rod_front_wins else "All Square (Halved)"
    
    rod_back_wins = hole_df['Rod Won'].max() - rod_front_wins
    jim_back_wins = hole_df['Jim Won'].max() - jim_front_wins
    back9_winner = f"Rod wins Back 9 by {rod_back_wins}" if rod_back_wins > jim_back_wins else f"Jim wins Back 9 by {jim_back_wins}" if jim_back_wins > rod_back_wins else "All Square (Halved)"
    
    rod_overall_wins = hole_df['Rod Won'].max()
    jim_overall_wins = hole_df['Jim Won'].max()
    overall_winner = f"Rod wins match by {rod_overall_wins - jim_overall_wins}" if rod_overall_wins > jim_overall_wins else f"Jim wins match by {jim_overall_wins - rod_overall_wins}" if jim_overall_wins > rod_overall_wins else "All Square"
    
    front_net = 1 if 'Rod wins' in front9_winner else -1 if 'Jim wins' in front9_winner else 0
    back_net = 1 if 'Rod wins' in back9_winner else -1 if 'Jim wins' in back9_winner else 0
    overall_net = 1 if 'Rod wins' in overall_winner else -1 if 'Jim wins' in overall_winner else 0
    rod_net = front_net + back_net + overall_net
    
    return front9_winner, back9_winner, overall_winner, rod_net, hole_df

# Load matches - chronological order for history table
matches_df = pd.read_sql('SELECT * FROM Matches ORDER BY date ASC', conn)

# Add this after st.title("Rod vs Jim Golf Match Tracker")
st.image(
    "Jimothy.png",   # ← change to your image filename (must be in the same folder as golf_app.py)
    caption="Jim - Chasing birdies since 2026 ⛳",  # optional caption
    use_column_width=True  # makes it full-width, looks great
)
# Second image right below it
st.image("Rod.jpg", 
         caption="Rod Victorious in Bandon", 
         use_column_width=True)

# Match History (oldest first)
st.subheader("Match History")
st.dataframe(
    matches_df.drop(columns=['match_id', 'sheet_name'], errors='ignore'),
    width='stretch',
    hide_index=True
)

# Scoring Averages per Match (total strokes on 18 holes, front 9, back 9)
st.subheader("Scoring Averages per Match")

# Query to sum scores per match
scores_query = """
SELECT 
    h.match_id,
    m.date,
    SUM(CASE WHEN h.hole_number <= 9 THEN h.rod_score ELSE 0 END) AS rod_front_total,
    SUM(CASE WHEN h.hole_number > 9 THEN h.rod_score ELSE 0 END) AS rod_back_total,
    SUM(h.rod_score) AS rod_total,
    SUM(CASE WHEN h.hole_number <= 9 THEN h.jim_score ELSE 0 END) AS jim_front_total,
    SUM(CASE WHEN h.hole_number > 9 THEN h.jim_score ELSE 0 END) AS jim_back_total,
    SUM(h.jim_score) AS jim_total
FROM Holes h
JOIN Matches m ON h.match_id = m.match_id
GROUP BY h.match_id
ORDER BY m.date
"""
match_scores = pd.read_sql(scores_query, conn)

if not match_scores.empty:
    total_matches = len(match_scores)

    rod_overall_avg = match_scores['rod_total'].mean()
    jim_overall_avg = match_scores['jim_total'].mean()
    rod_front_avg   = match_scores['rod_front_total'].mean()
    jim_front_avg   = match_scores['jim_front_total'].mean()
    rod_back_avg    = match_scores['rod_back_total'].mean()
    jim_back_avg    = match_scores['jim_back_total'].mean()

    # 4-column table data
    avg_table_data = {
        "Player": ["Rod", "Jim"],
        "Avg Score per Match (18 holes)": [f"{rod_overall_avg:.1f}", f"{jim_overall_avg:.1f}"],
        "Avg Front 9 Score": [f"{rod_front_avg:.1f}", f"{jim_front_avg:.1f}"],
        "Avg Back 9 Score": [f"{rod_back_avg:.1f}", f"{jim_back_avg:.1f}"]
    }

    # Build HTML
    html_avg = """
    <table style="width:100%; max-width:800px; border-collapse: collapse; margin: 15px auto; font-family: Arial, sans-serif; font-size: 15px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
        <tr style="background-color: #1B5E20; color: white;">
            <th style="border: 1px solid #388E3C; padding: 10px; text-align: left;">Player</th>
            <th style="border: 1px solid #388E3C; padding: 10px; text-align: center;">Avg Score per Match (18 holes)</th>
            <th style="border: 1px solid #388E3C; padding: 10px; text-align: center;">Avg Front 9 Score</th>
            <th style="border: 1px solid #388E3C; padding: 10px; text-align: center;">Avg Back 9 Score</th>
        </tr>
    """
    for i, row in enumerate(zip(
        avg_table_data["Player"],
        avg_table_data["Avg Score per Match (18 holes)"],
        avg_table_data["Avg Front 9 Score"],
        avg_table_data["Avg Back 9 Score"]
    )):
        bg = "#E8F5E9" if i % 2 == 1 else "white"
        html_avg += f"""
        <tr style="background-color: {bg};">
            <td style="border: 1px solid #A5D6A7; padding: 10px; font-weight: bold;">{row[0]}</td>
            <td style="border: 1px solid #A5D6A7; padding: 10px; text-align: center;">{row[1]}</td>
            <td style="border: 1px solid #A5D6A7; padding: 10px; text-align: center;">{row[2]}</td>
            <td style="border: 1px solid #A5D6A7; padding: 10px; text-align: center;">{row[3]}</td>
        </tr>
        """
    html_avg += "</table>"

    # THIS LINE MUST HAVE THE FLAG!
    st.components.v1.html(html_avg, height=300, scrolling=False)
    

    st.caption(f"Based on {total_matches} full matches. Lower scores are better.")
else:
    st.info("No match score data available yet.")
# Lifetime Summary
st.subheader("Lifetime Summary")

total_matches = len(matches_df)
rod_grand = matches_df['rod_net'].sum() if 'rod_net' in matches_df.columns and not matches_df.empty else 0
jim_grand = matches_df['jim_net'].sum() if 'jim_net' in matches_df.columns and not matches_df.empty else 0

def compute_rod_net(series):
    rod_wins = sum(1 for val in series if pd.notna(val) and 'Rod' in str(val))
    jim_wins = sum(1 for val in series if pd.notna(val) and 'Jim' in str(val))
    return rod_wins - jim_wins

rod_front_net = compute_rod_net(matches_df['front9_winner'])
rod_back_net = compute_rod_net(matches_df['back9_winner'])
rod_overall_net = compute_rod_net(matches_df['overall_winner'])

# Debug prints to Command Prompt
print(f"DEBUG - rod_front_net: {rod_front_net} (type: {type(rod_front_net)})")
print(f"DEBUG - rod_back_net: {rod_back_net} (type: {type(rod_back_net)})")
print(f"DEBUG - rod_overall_net: {rod_overall_net} (type: {type(rod_overall_net)})")
print(f"DEBUG - rod_grand: {rod_grand} (type: {type(rod_grand)})")
print(f"DEBUG - jim_grand: {jim_grand} (type: {type(jim_grand)})")

# Safe string conversion with $ formatting
rows = []
for cat, raw_val in [
    ("Front 9 – Rod Total", rod_front_net),
    ("Front 9 – Jim Total", -rod_front_net),
    ("Back 9 – Rod Total", rod_back_net),
    ("Back 9 – Jim Total", -rod_back_net),
    ("Overall – Rod Total", rod_overall_net),
    ("Overall – Jim Total", -rod_overall_net),
    ("Grand Total – Rod", rod_grand),
    ("Grand Total – Jim", jim_grand),
    ("Matches Played", total_matches)
]:
    if cat == "Matches Played":
        formatted_val = str(raw_val)
    else:
        val = int(raw_val)  # ensure plain int
        if val > 0:
            formatted_val = f"+${val}"
        elif val < 0:
            formatted_val = f"-${abs(val)}"
        else:
            formatted_val = "$0"
    
    rows.append((cat, formatted_val))

# HTML table - no Pandas DataFrame involved
html = """
<table style="width:100%; border-collapse: collapse; margin-top: 20px; font-family: Arial, sans-serif; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <tr style="background-color: #2E7D32; color: white;">
        <th style="border: 1px solid #ddd; padding: 12px; text-align: left; font-weight: bold;">Category</th>
        <th style="border: 1px solid #ddd; padding: 12px; text-align: right; font-weight: bold;">Value</th>
    </tr>
"""
for i, (cat, val) in enumerate(rows):
    bg = "#f9f9f9" if i % 2 == 1 else "white"
    html += f"""
    <tr style="background-color: {bg};">
        <td style="border: 1px solid #ddd; padding: 12px; color: #333;">{cat}</td>
        <td style="border: 1px solid #ddd; padding: 12px; text-align: right; font-weight: bold; color: {'#D32F2F' if '-' in str(val) else '#388E3C'};">{val}</td>
    </tr>
    """
html += "</table>"

st.components.v1.html(html, height=400, scrolling=True)

# Individual Rounds (newest first for quick access)
st.subheader("Individual Rounds")
for _, match in matches_df[::-1].iterrows():  # Reverse for newest at top
    with st.expander(f"{match['date']} - {match['overall_winner']}"):
        holes_df = pd.read_sql(f"SELECT * FROM Holes WHERE match_id = {match['match_id']}", conn)
        st.dataframe(
            holes_df.drop(columns=['hole_id', 'match_id'], errors='ignore'),
            width='stretch',
            hide_index=True
        )

# Add new match
st.subheader("Add New Match")
if 'form_cleared' not in st.session_state:
    st.session_state.form_cleared = False

new_date = st.text_input("Date (e.g., Feb 14 26)", key="new_date_input")
if new_date:
    hole_numbers = list(range(1, 19))
    default_df = pd.DataFrame({
        'Hole': hole_numbers,
        'Rod Score': [0] * 18,
        'Jim Score': [0] * 18,
        'Hole Winner': [''] * 18,
        'Match Status': [''] * 18,
        'Rod Won': [0] * 18,
        'Jim Won': [0] * 18
    })
    if st.session_state.form_cleared:
        edited_df = st.data_editor(default_df, num_rows="fixed", hide_index=True, key="new_holes")
        st.session_state.form_cleared = False
    else:
        edited_df = st.data_editor(default_df, num_rows="fixed", hide_index=True, key="new_holes")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Calculate & Save Match"):
            front9, back9, overall, rod_net, updated_df = calculate_summaries(edited_df)
            jim_net = -rod_net
            cur.execute('''
            INSERT INTO Matches (date, sheet_name, front9_winner, back9_winner, overall_winner, rod_net, jim_net)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (new_date, '', front9, back9, overall, rod_net, jim_net))
            new_match_id = cur.lastrowid
            for _, row in updated_df.iterrows():
                cur.execute('''
                INSERT INTO Holes (match_id, hole_number, rod_score, jim_score, hole_winner, match_status, rod_won_cum, jim_won_cum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (new_match_id, row['Hole'], row['Rod Score'], row['Jim Score'], row['Hole Winner'], row['Match Status'], row['Rod Won'], row['Jim Won']))
            conn.commit()
            st.success("Match saved! Refresh to see updates.")
            st.session_state.form_cleared = True
            st.rerun()
    with col2:
        if st.button("Clear Form"):
            st.session_state.form_cleared = True
            st.rerun()

conn.close()