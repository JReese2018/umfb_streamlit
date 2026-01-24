## To run the program use the below comment in the terminal(crtl+`)
## streamlit run main.py

import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit_authenticator as stauth
import urllib
import datetime
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt

from functions import get_player_force_plate_data, get_position_force_plate_data, get_catapult_data, get_body_weight_data, get_internal_load_data, get_player_perch_data, get_position_perch_data, get_max_for_exercise, get_hydration_data, filter_dates, get_percentile_data

today = datetime.date.today()
st.set_page_config(initial_sidebar_state="expanded", page_icon='https://a.espncdn.com/combiner/i?img=/i/teamlogos/ncaa/500/2390.png&h=200&w=200', page_title='Sport Science Player Dashboard')

## CSS Styling
st.markdown("""
    <style>
        .percentile-badge {
            font-size: 2rem;
            font-weight: 700;
            padding: 1rem;
            border-radius: 0.5rem;
            text-align: center;
            margin: 0.5rem 0;
        }
        .percentile-high {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
        }
        .percentile-middle {
            background: linear-gradient(135deg, #facc15 0%, #eab308 100%);
            color: white;
        }
        .percentile-low {
            background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)
## Database connection
## Connection settings
server = 'sportsciencefb.database.windows.net'
database = 'sportsciencefb'
username = 'um_sport_science'
password = 'MiamiF00tball!'

## Connection Build to Azure
params = urllib.parse.quote_plus(
    f"DRIVER=ODBC Driver 18 for SQL Server;"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
    "MARS_Connection=yes;"
)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")


## User Authentication
## For this part we might just get the names from the database and put them in a list
get_players_sql_string = '''
select playerid, Player, positionID, app_username, app_password
from player p 
'''

get_players_sql_query = text(get_players_sql_string)
with engine.connect() as conn:
    player_df = pd.read_sql(get_players_sql_query, conn)
    player_df = player_df.dropna()
    names = player_df['Player'].to_list()
    usernames = player_df['app_username'].tolist()
    passwords = player_df['app_password'].tolist()
    playerids = player_df['playerid'].tolist()
    positionids = player_df['positionID'].tolist()


## Formatting for credentials
credentials = {"usernames": {}}
for name, playerid, positionid, username, password in zip(names, playerids, positionids, usernames, passwords):
    credentials["usernames"][username] = {
        "name": name,
        "playerid" : playerid,
        "positionid" : positionid,
        "password": password
    }

authenticator = stauth.Authenticate(credentials, 'player_dashboard', 'player_dashboard_key', cookie_expiry_days=7, auto_hash=False)


try:
    authenticator.login()
    st.session_state['playerid'] = None
except Exception as e:
    st.error(e)

if st.session_state.get('authentication_status'):
    full_name = st.session_state.get("name")
    name = full_name.split()[-1]
    username = st.session_state.get('username')
    ## Getting playerID (This will be used to query the data specifially for the user which will speed up the program significantly)
    playerid = player_df.loc[player_df['app_username'] == username]['playerid'].iloc[0]
    positionid = player_df.loc[player_df['app_username'] == username]['positionID'].iloc[0]
    st.session_state["playerid"] = playerid

    ## Player Force Plate Data
    player_peak_cmj_jump, player_peak_cmj_date, cmj_df = get_player_force_plate_data(engine, playerid)
    ## Position Force Plate Data (2025)
    raw_position_cmj_df, position_cmj_df_line, position_name, position_cmj_df = get_position_force_plate_data(engine, positionid)
    ## Highest Jump Height for Position
    position_cmj_df = position_cmj_df.sort_values(['Jump Height']).tail(1)
    highest_position_jump = position_cmj_df['Jump Height'].iloc[0]
    highest_position_date = position_cmj_df['Date'].iloc[0]
    highest_position_player = position_cmj_df['playerID'].iloc[0]
    highest_position_player = player_df.loc[player_df['playerid'] == highest_position_player]['Player'].iloc[0]
    split_name = highest_position_player.split()
    highest_position_player = " ".join([split_name[-1]] + split_name[:-1])
    ## Catapult Data
    catapult_df = get_catapult_data(engine, playerid)
    ## Body Weight Data
    body_weight_df = get_body_weight_data(engine, playerid)
    ## Internal Load Data
    internal_df = get_internal_load_data(engine, playerid)
    ## Perch Data
    player_perch_df = get_player_perch_data(engine, playerid)
    ## Position Perch Data (2025)
    position_perch_df = get_position_perch_data(engine, positionid)
    ## Hydration Data
    hydration_df = get_hydration_data(engine, playerid)
    ## To get the position line for the weights graph
    position_perch_df_data = position_perch_df.groupby(['Date', 'exerciseID']).mean(numeric_only=True).reset_index()[['Date', 'exerciseID', 'Weight (lbs)', 'Set Avg Peak Velocity (m/s)']]
    ## Player Weight Room Max
    player_bench_max, player_bench_max_date = get_max_for_exercise(player_perch_df, 1)
    player_squat_max, player_squat_max_date = get_max_for_exercise(player_perch_df, 4)
    player_power_clean_max, player_power_clean_max_date = get_max_for_exercise(player_perch_df, 9)

    ## Baseline Data and Player Max Weight Room data
    latest_weight = body_weight_df.tail(1)['Weight'].iloc[0]
    latest_bf = body_weight_df.tail(1)['BF%'].iloc[0]
    latest_hydration = hydration_df.tail(1)['Hydration Status'].iloc[0]
    latest_hydration_date = hydration_df.tail(1)['Date'].iloc[0]
    data = {'Metric' : ['Body Weight (lbs)', 'Body Fat (%)', 'Latest Hydration Status'], 'Value' : [latest_weight, latest_bf, latest_hydration]}
    baseline_df = pd.DataFrame(data)

    data = {'Lift' : ['Bench', 'Back Squat', 'Power Clean'], 'Value' : [player_bench_max, player_squat_max, player_power_clean_max], 'Date' : [player_bench_max_date, player_squat_max_date, player_power_clean_max_date]}
    max_df = pd.DataFrame(data)


    ## Heart Variability Composity
    hr_var = internal_df[['Date', 'SDNN', 'RMSSD']]
    hr_var['HR Variability'] = (hr_var['SDNN'] + hr_var['RMSSD']) / 2
    
    ########## SIDE BAR ##########
    with st.sidebar:
        st.subheader("Options")
        toggle_positon_avg = st.checkbox("Position Avg (Jump Height and Weight Room)", value=True)
        toggle_data_labels = st.checkbox("Data Labels")

        ## Logout button
        authenticator.logout()

    ########## USER INTERFACE ##########
    ## Name and Logo
    col1, col2 = st.columns([0.95, 0.05])
    with col1:
        st.title(f'Welcome {name}! Today is {today.strftime("%m/%d/%Y")}')
    with col2:
        st.image('https://a.espncdn.com/combiner/i?img=/i/teamlogos/ncaa/500/2390.png&h=200&w=200')
    
    
    ## Baseline and Max Data
    col1, col2, = st.columns(2)

    with col1:
        st.subheader('Current Baseline')
        st.dataframe(data=baseline_df, hide_index=True)

    with col2:
        st.subheader("Max Weight Room Stats")
        st.dataframe(data=max_df, hide_index=True)

    ## Hydration
    st.subheader('Latest Hydration Status:')
    st.subheader(f"{latest_hydration} on {latest_hydration_date.strftime("%m/%d/%Y")}")

    ## Hydration Pie Chart
    hydrated_counts = len(hydration_df.loc[hydration_df['Hydration Status'] == 'Hydrated'])
    mildly_dehydrated_counts = len(hydration_df.loc[hydration_df['Hydration Status'] == 'Mildly Dehydrated'])
    moderately_dehydrated_counts = len(hydration_df.loc[hydration_df['Hydration Status'] == 'Moderately Dehydrated'])
    severely_dehydrated_counts = len(hydration_df.loc[hydration_df['Hydration Status'] == 'Severely Dehydrated'])
    hydration_counts = [hydrated_counts, mildly_dehydrated_counts, moderately_dehydrated_counts, severely_dehydrated_counts]
    hydration_labels = ['Hydrated', 'Mildly Dehydrated', 'Moderately Dehydrated', 'Severely Dehydrated']
    hydration_colors = ['#005030', '#B19200', '#F47321', '#FF0000']
    ## Created dataframe to eliminate 0 values
    hydration_pie_df = pd.DataFrame({'Counts': hydration_counts, 'Labels': hydration_labels, 'Colors': hydration_colors})
    hydration_pie_df = hydration_pie_df.loc[hydration_pie_df['Counts'] > 0]
    ## Creating shell of plot and coloring
    try:
        fig, ax = plt.subplots(figsize=(12, 4), linewidth=2, edgecolor='#6F7B6F')
        fig.set_facecolor("#191b18")
        ax.set_facecolor("#191b18")
        ax.pie(hydration_pie_df['Counts'], labels=hydration_pie_df['Labels'], colors=hydration_pie_df['Colors'], wedgeprops=dict(width=0.5, edgecolor='black'), textprops={'color': '#C9CFC9'}, autopct='%1.1f%%', pctdistance=0.75)
        ax.set_title(f"{name}'s Hydration Distribution", color='#C9CFC9')
        st.pyplot(fig)
    except:
        None

    hydration_url = "https://www.google.com"
    st.write("Stay game-ready: learn how to optimize your hydration [here](%s)." % hydration_url)
    st.caption(':blue[DEV NOTE]: This goes to Google for now until we get a resource(s) that is good for the athletes to look at.')

    st.title('Physical Data')
    ## Creating Slider
    date_min = datetime.date(2025, 1, 1)
    date_max = today
    default_min = today - datetime.timedelta(days=30)
    
    selected_date = st.slider(label="Select Date Range", min_value=date_min,max_value=date_max,value=(default_min, date_max))
    st.caption("This slider affects all of the graphs (Defaults to the last 30 days)")

    ## Filtering dates
    cmj_filtered_data = filter_dates(cmj_df, selected_date)
    position_cmj_filtered_data = filter_dates(position_cmj_df_line, selected_date)
    catapult_filtered_data = filter_dates(catapult_df, selected_date)
    catapult_filtered_data['Total Player Load'] = round(catapult_filtered_data['Total Player Load'])
    body_weight_filtered_data = filter_dates(body_weight_df, selected_date)
    internal_filtered_data = filter_dates(internal_df, selected_date)
    hr_var_filtered_data = filter_dates(hr_var, selected_date)
    perch_filtered_data = filter_dates(player_perch_df, selected_date)
    position_perch_filtered_data = filter_dates(position_perch_df_data, selected_date)


    ## Jump Height Graph
    st.header('Jump Height Data')
    try:
        if cmj_filtered_data.empty:
            raise IndexError
        ## Creating shell of plot and coloring
        fig, ax = plt.subplots(figsize=(12, 4), linewidth=2, edgecolor='#6F7B6F')
        ax.grid(color='#303631')
        fig.set_facecolor("#191b18")
        ax.set_facecolor("#191b18")
        for spine in ax.spines.values():
            spine.set_visible(False)
        ## Titles and Labels
        ax.set_xlabel('Date', color='#C9CFC9')
        ax.set_ylabel('Meters (m)', color='#C9CFC9')
        ax.tick_params(axis='x', colors='#C9CFC9', length=0, rotation=30)
        ax.tick_params(axis='y', colors='#C9CFC9', length=0)
        ax.set_title(f'Force Plate Jump Height Over Time', color='#C9CFC9')
        plt.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")

        ## Player and Position Lines
        if toggle_positon_avg == True:
            ax.plot(position_cmj_filtered_data['Date'], position_cmj_filtered_data['Jump Height'], color='#005030', marker='.', markersize=12, linestyle='--', label=f'{position_name} Avg')
        ax.plot(cmj_filtered_data['Date'], cmj_filtered_data['Jump Height'], color='#F47321', marker='.', markersize=12, linestyle='--', label='You')
        
        ## Checking for Options
        if toggle_data_labels == True and toggle_positon_avg == True: 
            #for i, (x, y) in enumerate(zip(position_cmj_filtered_data['Date'], position_cmj_filtered_data['Jump Height'])):
                #ax.annotate(f'{y:.2f}', xy=(x, y), xytext=(0, 5), textcoords='offset points', ha='center', fontsize=8, color='#C9CFC9')
            for i, (x, y) in enumerate(zip(cmj_filtered_data['Date'], cmj_filtered_data['Jump Height'])):
                ax.annotate(f'{y:.2f}', xy=(x, y), xytext=(0, 5), textcoords='offset points', ha='center', fontsize=8, color='#C9CFC9')
        elif toggle_data_labels == True:
            for i, (x, y) in enumerate(zip(cmj_filtered_data['Date'], cmj_filtered_data['Jump Height'])):
                ax.annotate(f'{y:.2f}', xy=(x, y), xytext=(0, 5), textcoords='offset points', ha='center', fontsize=8, color='#C9CFC9')
        
        ## Legend
        ax.legend()
        ## Showing Plot on App
        st.pyplot(fig)
        st.caption(f"You performed your highest jump in 2025 on {player_peak_cmj_date.strftime("%m/%d/%Y")} (**{player_peak_cmj_jump}m**)")
        st.caption(f"The Highest jump performed by your position ({position_name}) in 2025 was performed by **{highest_position_player}** on {highest_position_date.strftime("%m/%d/%Y")} (**{highest_position_jump}m**)")
    except:
        with st.container(border=True):
            st.markdown(f"<p style='text-align: center;'>No Data between {selected_date[0].strftime("%m/%d/%Y")} and {selected_date[1].strftime("%m/%d/%Y")}</h1>", unsafe_allow_html=True)
            st.caption(f"You performed your highest jump in 2025 on {player_peak_cmj_date.strftime("%m/%d/%Y")} (**{player_peak_cmj_jump}m**)")
            st.caption(f"The Highest jump performed by your position ({position_name}) in 2025 was performed by **{highest_position_player}** on {highest_position_date.strftime("%m/%d/%Y")} (**{highest_position_jump}m**)")
     
    ## Max Velocity Graph
    st.header('Max Velocity Data')
    try:
        if catapult_filtered_data.empty:
            raise IndexError
        ## Creating shell of plot and coloring
        fig, ax = plt.subplots(figsize=(12, 4), linewidth=2, edgecolor='#6F7B6F')
        ax.grid(color='#303631')
        fig.set_facecolor("#191b18")
        ax.set_facecolor("#191b18")
        for spine in ax.spines.values():
            spine.set_visible(False)
        ## Titles and Labels
        ax.set_xlabel('Date', color='#C9CFC9')
        ax.set_ylabel('Speed (MPH)', color='#C9CFC9')
        ax.tick_params(axis='x', colors='#C9CFC9', length=0, rotation=30)
        ax.tick_params(axis='y', colors='#C9CFC9', length=0)
        ax.set_title(f'Max Velocity Over Time', color='#C9CFC9')
        plt.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")
        ## Player and Position Lines
        ax.plot(catapult_filtered_data['Date'], catapult_filtered_data['Maximum Velocity'], color='#F47321', marker='.', markersize=12, linestyle='--')

        ## Checking for Options
        if toggle_data_labels == True:
            for i, (x, y) in enumerate(zip(catapult_filtered_data['Date'], catapult_filtered_data['Maximum Velocity'])):
                ax.annotate(f'{y:.2f}', xy=(x, y), xytext=(0, 5), textcoords='offset points', ha='center', fontsize=8, color='#C9CFC9')

        ## Showing Plot on App
        st.pyplot(fig)
    except:
        with st.container(border=True):
            st.markdown(f"<p style='text-align: center;'>No Data between {selected_date[0].strftime("%m/%d/%Y")} and {selected_date[1].strftime("%m/%d/%Y")}</h1>", unsafe_allow_html=True)
    
    ## Player Load Graph
    st.header('Player Load Data')
    try:
        if catapult_filtered_data.empty:
            raise IndexError
        
        ## Creating shell of plot and coloring
        fig, ax = plt.subplots(figsize=(12, 4), linewidth=2, edgecolor='#6F7B6F')
        ax.grid(color='#303631', zorder=0, axis='y')
        fig.set_facecolor("#191b18")
        ax.set_facecolor("#191b18")
        for spine in ax.spines.values():
            spine.set_visible(False)
        ## Titles and Labels
        ax.set_xlabel('Date', color='#C9CFC9')
        ax.set_ylabel('Player Load', color='#C9CFC9')
        ax.tick_params(axis='x', colors='#C9CFC9', length=0, rotation=30)
        ax.tick_params(axis='y', colors='#C9CFC9', length=0)
        ax.set_title(f'Player Load by Day', color='#C9CFC9')
        plt.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")
        ## Player and Position Lines
        bar = ax.bar(catapult_filtered_data['Date'], catapult_filtered_data['Total Player Load'], color='#F47321', edgecolor='#000000', linewidth=2, zorder=3, align='center')
        
        ## Checking for Options
        if toggle_data_labels == True:
            ax.bar_label(bar, color='#C9CFC9', padding=3)
        ## Showing Plot on App
        st.pyplot(fig)
    except:
        with st.container(border=True):
            st.markdown(f"<p style='text-align: center;'>No Data between {selected_date[0].strftime("%m/%d/%Y")} and {selected_date[1].strftime("%m/%d/%Y")}</h1>", unsafe_allow_html=True)
    
    ## Body Weight Graph
    st.header('Body Weight Data')
    try:
        if body_weight_filtered_data.empty:
            raise IndexError
        ## Creating shell of plot and coloring
        fig, ax = plt.subplots(figsize=(12, 4), linewidth=2, edgecolor='#6F7B6F')
        ax.grid(color='#303631')
        fig.set_facecolor("#191b18")
        ax.set_facecolor("#191b18")
        for spine in ax.spines.values():
            spine.set_visible(False)
        ## Titles and Labels
        ax.set_xlabel('Date', color='#C9CFC9')
        ax.set_ylabel('Weight (lbs)', color='#C9CFC9')
        ax.tick_params(axis='x', colors='#C9CFC9', length=0, rotation=30)
        ax.tick_params(axis='y', colors='#C9CFC9', length=0)
        ax.set_title(f'Body Weight Over Time', color='#C9CFC9')
        plt.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")

        ## Player Line
        ax.plot(body_weight_filtered_data['Date'], body_weight_filtered_data['Weight'], color='#F47321', marker='.', markersize=12, linestyle='--', label='You')
        
        ## Checking for Options
        if toggle_data_labels == True:
            for i, (x, y) in enumerate(zip(body_weight_filtered_data['Date'], body_weight_filtered_data['Weight'])):
                ax.annotate(round(y), xy=(x, y), xytext=(0, 5), textcoords='offset points', ha='center', fontsize=8, color='#C9CFC9')

        ## Showing Plot on App
        st.pyplot(fig)
    except:
        with st.container(border=True):
            st.markdown(f"<p style='text-align: center;'>No Data between {selected_date[0].strftime("%m/%d/%Y")} and {selected_date[1].strftime("%m/%d/%Y")}</h1>", unsafe_allow_html=True)
    
    
    ## Calories Burned Graph
    st.header('Caloric Expenditure Data')
    try:
        if internal_filtered_data.empty:
            raise IndexError
        ## Creating shell of plot and coloring
        fig, ax = plt.subplots(figsize=(12, 4), linewidth=2, edgecolor='#6F7B6F')
        ax.grid(color='#303631', zorder=0, axis='y')
        fig.set_facecolor("#191b18")
        ax.set_facecolor("#191b18")
        for spine in ax.spines.values():
            spine.set_visible(False)
        ## Titles and Labels
        ax.set_xlabel('Date', color='#C9CFC9')
        ax.set_ylabel('Calories (kcal)', color='#C9CFC9')
        ax.tick_params(axis='x', colors='#C9CFC9', length=0, rotation=30)
        ax.tick_params(axis='y', colors='#C9CFC9', length=0)
        ax.set_title(f'Calories Burned', color='#C9CFC9')
        plt.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")
        ## Player and Position Lines
        bar = ax.bar(internal_filtered_data['Date'], round(internal_filtered_data['Calories Burned']), color='#F47321', edgecolor='#000000', linewidth=2, zorder=3, align='center')
        
        ## Checking for Options
        if toggle_data_labels == True:
            ax.bar_label(bar, color='#C9CFC9', padding=3)
        ## Showing Plot on App
        st.pyplot(fig)
        st.caption(f"Average Calories Burned in range: **{round(internal_df.mean(numeric_only=True)['Calories Burned'])} cal**")
    except IndexError:
        with st.container(border=True):
            st.markdown(f"<p style='text-align: center;'>No Data between {selected_date[0].strftime("%m/%d/%Y")} and {selected_date[1].strftime("%m/%d/%Y")}</h1>", unsafe_allow_html=True)
    
    ## Heart Variability Graph
    st.header('Heart Rate Variability Data')
    try:
        if hr_var.empty:
            raise IndexError
        ## Creating shell of plot and coloring
        fig, ax = plt.subplots(figsize=(12, 4), linewidth=2, edgecolor='#6F7B6F')
        ax.grid(color='#303631')
        fig.set_facecolor("#191b18")
        ax.set_facecolor("#191b18")
        for spine in ax.spines.values():
            spine.set_visible(False)
        ## Titles and Labels
        ax.set_xlabel('Date', color='#C9CFC9')
        ax.set_ylabel('Score', color='#C9CFC9')
        ax.tick_params(axis='x', colors='#C9CFC9', length=0, rotation=30)
        ax.tick_params(axis='y', colors='#C9CFC9', length=0)
        ax.set_title(f'Heart Rate Variability Over Time', color='#C9CFC9')
        plt.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")

        ## Player Line
        ax.plot(hr_var_filtered_data['Date'], hr_var_filtered_data['HR Variability'], color='#F47321', marker='.', markersize=12, linestyle='--', label='You')
        
        ## Checking for Options
        if toggle_data_labels == True:
            for i, (x, y) in enumerate(zip(hr_var_filtered_data['Date'], hr_var_filtered_data['HR Variability'])):
                ax.annotate(round(y), xy=(x, y), xytext=(0, 5), textcoords='offset points', ha='center', fontsize=8, color='#C9CFC9')

        ## Showing Plot on App
        st.pyplot(fig)
    except IndexError:
        with st.container(border=True):
            st.markdown(f"<p style='text-align: center;'>No Data between {selected_date[0].strftime("%m/%d/%Y")} and {selected_date[1].strftime("%m/%d/%Y")}</h1>", unsafe_allow_html=True)
      
    ## Weight Room Data
    ## Bench
    st.header('Weight Room Data')
    st.subheader('Bench')
    try:
        if perch_filtered_data.empty:
            raise IndexError
        bench_data = round(perch_filtered_data.loc[perch_filtered_data['exerciseID'] == 1])
        position_bench_data = position_perch_filtered_data.loc[position_perch_filtered_data['exerciseID'] == 1]
        player_peak_bench = bench_data.sort_values(['Weight (lbs)']).tail(1)
        player_peak_bench_rep = player_peak_bench['Weight (lbs)'].iloc[0]
        player_peak_bench_date = player_peak_bench['Date'].iloc[0]
        

        ## Creating shell of plot and coloring
        fig, ax = plt.subplots(figsize=(12, 4), linewidth=2, edgecolor='#6F7B6F')
        ax.grid(color='#303631', zorder=0, axis='y')
        fig.set_facecolor("#191b18")
        ax.set_facecolor("#191b18")
        for spine in ax.spines.values():
            spine.set_visible(False)
        ## Titles and Labels
        ax.set_xlabel('Date', color='#C9CFC9')
        ax.set_ylabel('Weight (lbs)', color='#C9CFC9')
        ax.tick_params(axis='x', colors='#C9CFC9', length=0, rotation=30)
        ax.tick_params(axis='y', colors='#C9CFC9', length=0)
        ax.set_title(f'Bench Press Weight Over Time', color='#C9CFC9')
        plt.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")
        ## Position Line
        if toggle_positon_avg == True:
            ax2 = ax.twinx()
            ax2.plot(position_bench_data['Date'], position_bench_data['Weight (lbs)'], color='#005030', marker='.', markersize=12, linestyle='--', label=f'{position_name} Avg')
            for spine in ax2.spines.values():
                spine.set_visible(False)
            ax2.axis('off')
        ## Player Bar
        bar = ax.bar(bench_data['Date'], round(bench_data['Weight (lbs)']), color='#F47321', edgecolor='#000000', linewidth=2, zorder=3, align='center', label='You')
        
        ## The bar graph has to be created first to get its axis points so that is why we are checking the toggle again
        ## The reach the Position is created first is because matplotlib needs to have all of the dates that will be on the graph (which will be represented by the position line)
        ## Otherwise the dates will be out of order
        if toggle_positon_avg == True:
            ax2.set_xlim(ax.get_xlim()) 
            ax2.set_ylim(ax.get_ylim())
        
        ## Checking for Options
        if toggle_data_labels == True and toggle_positon_avg == True: 
            #for i, (x, y) in enumerate(zip(position_bench_data['Date'], position_bench_data['Weight (lbs)'])):
                #ax2.annotate(f'{y:.2f}', xy=(x, y), xytext=(0, 5), textcoords='offset points', ha='center', fontsize=8, color='#C9CFC9')
            ax.bar_label(bar, color='#C9CFC9', padding=3)
        elif toggle_data_labels == True:
            ax.bar_label(bar, color='#C9CFC9', padding=3)

        ## Legend
        fig.legend()
        ## Showing Plot on App
        st.pyplot(fig)
        st.caption(f"Heaviest Bench in range: **{round(player_peak_bench_rep)}lbs** on {player_peak_bench_date}")
    except IndexError:
        with st.container(border=True):
            st.markdown(f"<p style='text-align: center;'>No Data between {selected_date[0].strftime("%m/%d/%Y")} and {selected_date[1].strftime("%m/%d/%Y")}</h1>", unsafe_allow_html=True)
    
    ## Back Squat
    st.subheader('Back Sqaut')
    try:
        if perch_filtered_data.empty:
            raise IndexError
        squat_data = round(perch_filtered_data.loc[perch_filtered_data['exerciseID'] == 4])
        position_squat_data = position_perch_filtered_data.loc[position_perch_filtered_data['exerciseID'] == 4]
        player_peak_squat = squat_data.sort_values(['Weight (lbs)']).tail(1)
        player_peak_squat_rep = player_peak_squat['Weight (lbs)'].iloc[0]
        player_peak_squat_date = player_peak_squat['Date'].iloc[0]

        ## Creating shell of plot and coloring
        fig, ax = plt.subplots(figsize=(12, 4), linewidth=2, edgecolor='#6F7B6F')
        ax.grid(color='#303631', zorder=0, axis='y')
        fig.set_facecolor("#191b18")
        ax.set_facecolor("#191b18")
        for spine in ax.spines.values():
            spine.set_visible(False)
        ## Titles and Labels
        ax.set_xlabel('Date', color='#C9CFC9')
        ax.set_ylabel('Weight (lbs)', color='#C9CFC9')
        ax.tick_params(axis='x', colors='#C9CFC9', length=0, rotation=30)
        ax.tick_params(axis='y', colors='#C9CFC9', length=0)
        ax.set_title(f'Back Squat Weight Over Time', color='#C9CFC9')
        plt.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")
        ## Position Line
        if toggle_positon_avg == True:
            ax2 = ax.twinx()
            ax2.plot(position_squat_data['Date'], position_squat_data['Weight (lbs)'], color='#005030', marker='.', markersize=12, linestyle='--', label=f'{position_name} Avg')
            for spine in ax2.spines.values():
                spine.set_visible(False)
            ax2.axis('off')
        ## Player Bar
        bar = ax.bar(squat_data['Date'], round(squat_data['Weight (lbs)']), color='#F47321', edgecolor='#000000', linewidth=2, zorder=3, align='center', label='You')
        
        ## Checking for toggle to match line axis with bar axis
        if toggle_positon_avg == True:
            ax2.set_xlim(ax.get_xlim()) 
            ax2.set_ylim(ax.get_ylim())
        
        ## Checking for Options
        if toggle_data_labels == True and toggle_positon_avg == True: 
            #for i, (x, y) in enumerate(zip(position_squat_data['Date'], position_squat_data['Weight (lbs)'])):
                #ax2.annotate(f'{y:.2f}', xy=(x, y), xytext=(0, 5), textcoords='offset points', ha='center', fontsize=8, color='#C9CFC9')
            ax.bar_label(bar, color='#C9CFC9', padding=3)
        elif toggle_data_labels == True:
            ax.bar_label(bar, color='#C9CFC9', padding=3)

        ## Legend
        fig.legend()
        ## Showing Plot on App
        st.pyplot(fig)
        st.caption(f"Heaviest Squat in range: **{round(player_peak_squat_rep)}lbs** on {player_peak_squat_date}")
    except IndexError:
        with st.container(border=True):
            st.markdown(f"<p style='text-align: center;'>No Data between {selected_date[0].strftime("%m/%d/%Y")} and {selected_date[1].strftime("%m/%d/%Y")}</h1>", unsafe_allow_html=True)
    
    ## Power Clean
    st.subheader('Power Clean')
    try:
        if perch_filtered_data.empty:
            raise IndexError
        power_clean_data = round(perch_filtered_data.loc[perch_filtered_data['exerciseID'] == 9])
        position_power_clean_data = position_perch_filtered_data.loc[position_perch_filtered_data['exerciseID'] == 9]
        player_peak_power_clean = power_clean_data.sort_values(['Weight (lbs)']).tail(1)
        player_peak_power_clean_rep = player_peak_power_clean['Weight (lbs)'].iloc[0]
        player_peak_power_clean_date = player_peak_power_clean['Date'].iloc[0]

        ## Creating shell of plot and coloring
        fig, ax = plt.subplots(figsize=(12, 4), linewidth=2, edgecolor='#6F7B6F')
        ax.grid(color='#303631', zorder=0, axis='y')
        fig.set_facecolor("#191b18")
        ax.set_facecolor("#191b18")
        for spine in ax.spines.values():
            spine.set_visible(False)
        ## Titles and Labels
        ax.set_xlabel('Date', color='#C9CFC9')
        ax.set_ylabel('Weight (lbs)', color='#C9CFC9')
        ax.tick_params(axis='x', colors='#C9CFC9', length=0, rotation=30)
        ax.tick_params(axis='y', colors='#C9CFC9', length=0)
        ax.set_title(f'Power Clean Weight Over Time', color='#C9CFC9')
        plt.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")
        ## Position Line
        if toggle_positon_avg == True:
            ax2 = ax.twinx()
            ax2.plot(position_power_clean_data['Date'], position_power_clean_data['Weight (lbs)'], color='#005030', marker='.', markersize=12, linestyle='--', label=f'{position_name} Avg')
            for spine in ax2.spines.values():
                spine.set_visible(False)
            ax2.axis('off')
        ## Player Bar
        bar = ax.bar(power_clean_data['Date'], round(power_clean_data['Weight (lbs)']), color='#F47321', edgecolor='#000000', linewidth=2, zorder=3, align='center', label='You')
        
        ## Checking for toggle to match line axis with bar axis
        if toggle_positon_avg == True:
            ax2.set_xlim(ax.get_xlim()) 
            ax2.set_ylim(ax.get_ylim())
        
        ## Checking for Options
        if toggle_data_labels == True and toggle_positon_avg == True: 
            #for i, (x, y) in enumerate(zip(power_clean_data['Date'], power_clean_data['Weight (lbs)'])):
                #ax2.annotate(f'{y:.2f}', xy=(x, y), xytext=(0, 5), textcoords='offset points', ha='center', fontsize=8, color='#C9CFC9')
            ax.bar_label(bar, color='#C9CFC9', padding=3)
        elif toggle_data_labels == True:
            ax.bar_label(bar, color='#C9CFC9', padding=3)

        ## Legend
        fig.legend()
        ## Showing Plot on App
        st.pyplot(fig)
        st.caption(f"Heaviest Power Clean in range: **{round(player_peak_power_clean_rep)}lbs** on {player_peak_power_clean_date}")
    except IndexError:
        with st.container(border=True):
            st.markdown(f"<p style='text-align: center;'>No Data between {selected_date[0].strftime("%m/%d/%Y")} and {selected_date[1].strftime("%m/%d/%Y")}</h1>", unsafe_allow_html=True)

    ## Percentiles are going to be be the max
    
    ## Getting Max Values Percentiles
    player_max_cmj_percentile = get_percentile_data(raw_position_cmj_df, playerid)
    player_max_bench_percentile = get_percentile_data(position_perch_df, playerid, 1)
    player_max_squat_percentile = get_percentile_data(position_perch_df, playerid, 4)
    player_max_power_clean_percentile = get_percentile_data(position_perch_df, playerid, 9)

    percentiles_list = [player_max_cmj_percentile, player_max_bench_percentile, player_max_squat_percentile, player_max_power_clean_percentile]
    percentile_names_list = ['CMJ', 'Bench', 'Squat', 'Power Clean']
    percentile_df = pd.DataFrame({'Metric': percentile_names_list, 'Percentile': percentiles_list})
    
    ## Percentile Graph
    st.subheader('Percentile Ranking')
    st.caption('This is how you rank against your teammates in your position using the your max value that has been recorded')
    ## Creating shell of plot and coloring
    fig, ax = plt.subplots(figsize=(12, 4), linewidth=2, edgecolor='#6F7B6F')
    ax.grid(color='#303631', zorder=0, axis='y')
    fig.set_facecolor("#191b18")
    ax.set_facecolor("#191b18")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ## Titles and Labels
    ax.set_xlabel('Metric', color='#C9CFC9')
    ax.set_ylabel('Percentile', color='#C9CFC9')
    ax.tick_params(axis='x', colors='#C9CFC9', length=0)
    ax.tick_params(axis='y', colors='#C9CFC9', length=0)
    ax.set_title(f'{name} - {position_name} - Percentile Rankings against Position', color='#C9CFC9')
    plt.ylim(0, 100)
    ## Ordering 
    percentile_df = percentile_df.sort_values(['Percentile'], ascending=False)
    ## Getting colors of bars
    col = []
    for val in percentile_df['Percentile']:
        if val <= 25:
            col.append('red')
        elif val > 25 and val < 76:
            col.append('yellow')
        else:
            col.append('green')
    ## Player Bar
    bar = ax.bar(percentile_df['Metric'], percentile_df['Percentile'], color=col, edgecolor='#000000', linewidth=2, zorder=3, align='center', label='You')
    
    ## Checking for Options
    if toggle_data_labels == True and toggle_positon_avg == True: 
        #for i, (x, y) in enumerate(zip(power_clean_data['Date'], power_clean_data['Weight (lbs)'])):
            #ax2.annotate(f'{y:.2f}', xy=(x, y), xytext=(0, 5), textcoords='offset points', ha='center', fontsize=8, color='#C9CFC9')
        ax.bar_label(bar, color='#C9CFC9', padding=3, fmt='%.0f%%')
    elif toggle_data_labels == True:
        ax.bar_label(bar, color='#C9CFC9', padding=3)
    ## Showing Plot on App
    st.pyplot(fig)

    overall_rating = sum(percentiles_list) / len(percentiles_list)
    if overall_rating <= 25:
        background_color = 'percentile-low'
    elif overall_rating > 25 and overall_rating < 76:
        background_color = 'percentile-middle'
    else:
        background_color = 'percentile-high'
    st.markdown(f"""
                    <div class="percentile-badge {background_color}">
                        Overall Rating: {overall_rating}%
                    </div>
                    """, unsafe_allow_html=True)
    st.caption('The Overall Rating is the average of all of the percentiles recorded above. It is a representation of how you compare it in the weight room against your peers. It is not a representation of actual football skill.')
    st.caption(':blue[DEV NOTE]: This was made with the idea of integrating statsbomb or other actual player data and compare them against the rest of the FBS/ACC')
## If logging in fails
elif st.session_state.get('authentication_status') is False:
    st.error('Username/password is incorrect')
elif st.session_state.get('authentication_status') is None:
    st.warning('Please enter your username and password')



## 0-25% is red
## 26-75% is yellow
## 76-100% is green