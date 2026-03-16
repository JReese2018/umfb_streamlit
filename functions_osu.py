from sqlalchemy import create_engine, text
import pandas as pd

## Player Force Plate Data
def get_player_force_plate_data(playerid):
    cmj_df = pd.read_csv('data files/cmj.csv')
    cmj_df = cmj_df[['date', 'playerID', 'Jump Height']]
    cmj_df.rename(columns={'date' : 'Date'}, inplace=True)
    cmj_df = cmj_df.loc[cmj_df['playerID'] == playerid]

    cmj_df = cmj_df.sort_values(['Date'])
    player_peak_cmj = cmj_df.sort_values(['Jump Height']).tail(1)
    player_peak_cmj_jump = player_peak_cmj['Jump Height'].iloc[0]
    player_peak_cmj_date = player_peak_cmj['Date'].iloc[0]
    return player_peak_cmj_jump, player_peak_cmj_date, cmj_df

## Position Force Plate Data (2025)
def get_position_force_plate_data(positionid):
    position_cmj_df = pd.read_csv('data files/cmj.csv')
    merge_player = pd.read_csv('data files/player_with_credentials.csv')
    merge_position = pd.read_csv('data files/positions.csv')
    position_cmj_df = position_cmj_df.merge(merge_player, on='playerID')
    position_cmj_df = position_cmj_df.merge(merge_position, on='positionID')
    position_cmj_df = position_cmj_df.loc[position_cmj_df['positionID'] == positionid]
    position_cmj_df = position_cmj_df.loc[position_cmj_df['date'] > '2025-01-01']
    position_cmj_df = position_cmj_df[['playerID', 'Position', 'date', 'Jump Height']]
    position_cmj_df.rename(columns={'date' : 'Date'}, inplace=True)

    raw_position_cmj_df = position_cmj_df.sort_values(['Date'])

    ## To get the position line for the jump height graph
    position_cmj_df_line = raw_position_cmj_df.groupby('Date').mean(numeric_only=True).reset_index()[['Date', 'Jump Height']]
    ## Storing position in variable to remove column
    position_name = raw_position_cmj_df.tail(1)['Position'].iloc[0]
    position_cmj_df = raw_position_cmj_df.groupby(['Date', 'playerID']).max(numeric_only=True).reset_index()
    return raw_position_cmj_df, position_cmj_df_line, position_name, position_cmj_df

## Catapult Data
def get_catapult_data(playerid):
    catapult_df = pd.read_csv('data files/catapult.csv')
    catapult_df = catapult_df.loc[catapult_df['playerID'] == playerid]
    catapult_df = catapult_df[['playerID', 'Date', 'Total Player Load', 'Maximum Velocity']]
    df = catapult_df.groupby(['Date']).agg({'Total Player Load' : 'sum', 'Maximum Velocity' : 'max'}).reset_index().sort_values(['Date'])
    return df

def get_body_weight_data(playerid):
    body_weight_df = pd.read_csv('data files/body_weight.csv')
    ## This dropna is new by the way
    body_weight_df = body_weight_df.dropna(subset='Weight')
    body_weight_df = body_weight_df.loc[body_weight_df['playerID'] == playerid]
    body_weight_df = body_weight_df[['playerID', 'date', 'Weight', 'Ideal Weight', 'BF%']]
    body_weight_df.rename(columns={'date' : 'Date'}, inplace=True)
    ## Getting average because of the double weigh ins (During Camp)
    df = body_weight_df.groupby(['Date']).mean().reset_index().sort_values(['Date'])
    return df

## Internal Load Data
def get_internal_load_data(playerid):
    internal_df = pd.read_csv('data files/internalload2.csv')
    internal_df = internal_df.loc[internal_df['playerID'] == playerid]
    internal_df = internal_df[['playerID', 'Practice Date', 'SDNN', 'RMSSD', 'Calories Burned']]
    internal_df.rename(columns={'Practice Date' : 'Date'}, inplace=True)
    df = internal_df.sort_values(['Date'])
    return df

## Perch Data
def get_player_perch_data(playerid):
    perch_df = pd.read_csv('data files/perch.csv')
    perch_df = perch_df.loc[perch_df['playerID'] == playerid]
    perch_df = perch_df[['playerID', 'date', 'exerciseID', 'Weight (lbs)', 'Set Avg Peak Velocity (m/s)']]
    perch_df.rename(columns={'date' : 'Date'}, inplace=True)
    df = perch_df.groupby(['Date', 'exerciseID']).mean(numeric_only=True).reset_index().sort_values(['Date'])
    return df

## Position Perch Data (2025)
def get_position_perch_data(positionid):
    position_perch_df = pd.read_csv('data files/perch.csv')
    merge_player = pd.read_csv('data files/player_with_credentials.csv')
    merge_position = pd.read_csv('data files/positions.csv')
    position_perch_df = position_perch_df.merge(merge_player, on='playerID')
    position_perch_df = position_perch_df.merge(merge_position, on='positionID')
    position_perch_df = position_perch_df.loc[position_perch_df['positionID'] == positionid]
    position_perch_df = position_perch_df.loc[position_perch_df['date'] > '2025-01-01']
    position_perch_df = position_perch_df[['playerID', 'Position', 'date', 'exerciseID', 'Weight (lbs)', 'Set Avg Peak Velocity (m/s)']]
    position_perch_df.rename(columns={'date' : 'Date'}, inplace=True)
    df = position_perch_df.sort_values(['Date'])
    return df
    
## Hydration Data
def get_hydration_data(playerid):
    hydration_df = pd.read_csv('data files/hydration.csv')
    merge_status = pd.read_csv('data files/hydration_status.csv')
    hydration_df = hydration_df.merge(merge_status, on='hydration_statusID')
    hydration_df = hydration_df.loc[hydration_df['playerID'] == playerid]
    df = hydration_df[['playerID', 'Test Date', 'mOsm', 'Hydration Status']]
    df.rename(columns={'Test Date' : 'Date'}, inplace=True)
    return df

## Max Exercises
def get_max_for_exercise(df, exercise_id):
    try:
        subset = df.loc[df['exerciseID'] == exercise_id]
        if subset.empty:
            raise ValueError("No data for this exercise")

        best_row = subset.sort_values(['Weight (lbs)']).tail(1).iloc[0]
        weight = best_row['Weight (lbs)']
        date = best_row['Date'].strftime("%m/%d/%Y")

    except Exception:
        weight = 0
        date = 'N/A'

    return weight, date

## Filter Dates
def filter_dates(df, selected_date):
    filtered_data = round(df[(df['Date'] >= selected_date[0]) & (df['Date'] <= selected_date[1])], 2)
    filtered_data['Date'] = pd.to_datetime(filtered_data['Date']).dt.strftime("%m/%d/%Y")
    return filtered_data

## Percentiles
def get_percentile_data(df:pd.DataFrame, playerid:int, exercise:int=None):
    if 'exerciseID' in df.columns:
        try:
            percentile = round(df.loc[df['exerciseID'] == exercise].groupby(['playerID']).max(numeric_only=True)['Weight (lbs)'].rank(pct=True).reset_index().loc[df['playerID'] == playerid]['Weight (lbs)'].iloc[0]*100)
        except IndexError:
            percentile = 0
    ## CMJ
    else:
        try:
            percentile = round(df.groupby(['playerID']).max(numeric_only=True)['Jump Height'].rank(pct=True).reset_index().loc[df['playerID'] == playerid]['Jump Height'].iloc[0]*100)
        except IndexError:
            percentile = 0
    return percentile
