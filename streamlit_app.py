# Import packages
import streamlit as st
import pandas as pd
import requests
from snowflake.snowpark.functions import col

# -------------------------------
# App Title & Intro
# -------------------------------
st.title(':cup_with_straw: Customize Your Smoothie! :cup_with_straw:')
st.write("Choose the fruits you want in your custom Smoothie!")

# -------------------------------
# User Input
# -------------------------------
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# -------------------------------
# Snowflake Connection & Data
# -------------------------------
cnx = st.connection("snowflake")
session = cnx.session()

# Fetch both FRUIT_NAME and SEARCH_ON columns
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))

# Convert the Snowpark Dataframe to a Pandas Dataframe so we can use the LOC function
pd_df = my_dataframe.to_pandas()

# Optional: uncomment to debug
# st.dataframe(pd_df)
# st.stop()

# -------------------------------
# Multiselect
# -------------------------------
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    my_dataframe,
    max_selections=5
)

# -------------------------------
# Process Selection & API Call
# -------------------------------
if ingredients_list:
    
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        
        # Build ingredients string for the final database insert
        ingredients_string += fruit_chosen + ' '

        # Use Pandas LOC function to get the correct SEARCH_ON value
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        
        # Display the search value to the app (as requested by the course)
        st.write('The search value for ', fruit_chosen,' is ', search_on, '.')

        # Fetch nutrition info from Fruityvice API using the SEARCH_ON value
        st.subheader(fruit_chosen + ' Nutrition Information')
        fruityvice_response = requests.get("https://fruityvice.com/api/fruit/" + search_on)
        
        # Display the JSON results as a dataframe
        st.dataframe(data=fruityvice_response.json(), use_container_width=True)

    # -------------------------------
    # Insert Order into Snowflake
    # -------------------------------
    # The submit button should only appear if they have chosen ingredients
    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        # We also want to make sure they entered a name before inserting!
        if name_on_order:
            try:
                session.sql(
                    "INSERT INTO smoothies.public.orders (ingredients, name_on_order) VALUES (?, ?)",
                    params=[ingredients_string.strip(), name_on_order]
                ).collect()
                
                st.success(f'Your Smoothie is ordered, {name_on_order}!', icon='✅')
            except Exception as e:
                st.error(f"Insert failed: {e}")
        else:
            st.warning("Please enter the name for the smoothie before submitting.")
