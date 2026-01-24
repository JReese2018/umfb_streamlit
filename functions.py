from sqlalchemy import create_engine, text
import pandas as pd

## Player Force Plate Data
def get_player_force_plate_data(engine, playerid):
    query_string = f'''
    select playerID, date as "Date", [Jump Height]
    from cmj
    where playerID = {playerid}
    '''
    query = text(query_string)
    with engine.connect() as conn:
        cmj_df = pd.read_sql(query, conn)
    cmj_df = cmj_df.sort_values(['Date']).groupby(['Date']).mean().reset_index()
    player_peak_cmj = cmj_df.sort_values(['Jump Height']).tail(1)
    player_peak_cmj_jump = player_peak_cmj['Jump Height'].iloc[0]
    player_peak_cmj_date = player_peak_cmj['Date'].iloc[0]
    return player_peak_cmj_jump, player_peak_cmj_date, cmj_df

## Position Force Plate Data (2025)
def get_position_force_plate_data(engine, positionid):
    query_string = f'''
    select p.playerID, pos.[Position], c.[date] as "Date", c.[Jump Height]
    from cmj c
    join player p on c.playerID=p.playerid 
    JOIN positions pos ON p.positionID = pos.positionID
    where p.positionID = {positionid} AND c.[date] > '2025-01-01'
    '''
    query = text(query_string)
    with engine.connect() as conn:
        raw_position_cmj_df = pd.read_sql(query, conn).sort_values(['Date'])

    ## To get the position line for the jump height graph
    position_cmj_df_line = raw_position_cmj_df.groupby('Date').mean(numeric_only=True).reset_index()[['Date', 'Jump Height']]
    ## Storing position in variable to remove column
    position_name = raw_position_cmj_df.tail(1)['Position'].iloc[0]
    position_cmj_df = raw_position_cmj_df.groupby(['Date', 'playerID']).max(numeric_only=True).reset_index()
    return raw_position_cmj_df, position_cmj_df_line, position_name, position_cmj_df

## Catapult Data
def get_catapult_data(engine, playerid):
    query_string = f'''
    select playerID, Date, [Total Player Load], [Maximum Velocity]
    from catapult
    where playerID = {playerid}
    '''
    query = text(query_string)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn).groupby(['Date']).agg({'Total Player Load' : 'sum', 'Maximum Velocity' : 'max'}).reset_index().sort_values(['Date'])
    return df

def get_body_weight_data(engine, playerid):
    query_string = f'''
    select playerID, Date, Weight, [Ideal Weight], [BF%]
    from body_weight
    where playerID = {playerid}
    '''
    query = text(query_string)
    with engine.connect() as conn:
        ## Getting average because of the double weigh ins (During Camp)
        df = pd.read_sql(query, conn).groupby(['Date']).mean().reset_index().sort_values(['Date'])
    return df

## Internal Load Data
def get_internal_load_data(engine, playerid):
    query_string = f'''
    select playerID, [Practice Date] as "Date", SDNN, RMSSD, [Calories Burned]
    from internalload2
    where playerID = {playerid}
    '''
    query = text(query_string)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn).sort_values(['Date'])
    return df

## Perch Data
def get_player_perch_data(engine, playerid):
    query_string = f'''
    select playerID, date as "Date", exerciseID, [Weight (lbs)], [Set Avg Peak Velocity (m/s)]
    from perch
    where playerID = {playerid}
    '''
    query = text(query_string)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn).groupby(['Date', 'exerciseID']).mean(numeric_only=True).reset_index().sort_values(['Date'])
    return df

## Position Perch Data (2025)
def get_position_perch_data(engine, positionid):
    query_string = f'''
    select p.playerID, pos.[Position], per.[date] as "Date", per.exerciseID, per.[Weight (lbs)], per.[Set Avg Peak Velocity (m/s)]
    from perch per
    join player p on per.playerID=p.playerid 
    JOIN positions pos ON p.positionID = pos.positionID
    where p.positionID = {positionid} AND per.[date] > '2025-01-01'
    '''

    query = text(query_string)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn).sort_values(['Date'])
    return df
    
## Hydration Data
def get_hydration_data(engine, playerid):
    query_string = f'''
    select h.playerID, h.[Test Date] as "Date", h.mOsm, hs.[Hydration Status]
    from hydration h
    join hydration_status hs on hs.hydration_statusID=h.hydration_statusID
    where playerID = {playerid}
    '''
    query = text(query_string)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn).sort_values(['Date'])
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
