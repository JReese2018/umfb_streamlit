import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit_authenticator as stauth


## User Authentication

## For this part we might just get the names from the database and put them in a list
## We could even make a new column in the player table called something like "App Password"
names = ['Carson Beck', 'Keelan Marion']
usernames = ['CarsonBeck', 'KeelanMarion']
playerid = ['292', '321']
passwords = ['CBeck11', 'KMarion0']


## Formatting for credentials
credentials = {"usernames": {}}
for name, username, password in zip(names, usernames, passwords):
    credentials["usernames"][username] = {
        "name": name,
        "playerID" : playerid,
        "password": password
    }


authenticator = stauth.Authenticate(credentials, 'player_dashboard', 'player_dashboard_key', cookie_expiry_days=7)

try:
    authenticator.login()
except Exception as e:
    st.error(e)

if st.session_state.get('authentication_status'):
    name = st.session_state.get("name")
    ## Logout button
    authenticator.logout()
    st.write(f'Welcome {name}')
    st.title('Some content')
elif st.session_state.get('authentication_status') is False:
    st.error('Username/password is incorrect')
elif st.session_state.get('authentication_status') is None:
    st.warning('Please enter your username and password')










'''
## Checking authentication
if authentication_status == False:
    st.error("Username/password is incorrect. If problem persists, contact [person]")
if authentication_status == None:
    st.warning("Please enter your username and password")

if authentication_status:
    ## Run program
    
    ## Sidebar
    st.sidebar.header(f"Welcome {name}!")
    authenticator.logout("Logout", "sidebar")

'''