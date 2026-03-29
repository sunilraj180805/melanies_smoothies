# Import packages
import streamlit as st
import pandas as pd
import requests
from snowflake.snowpark.functions import col

# -------------------------------
# App Title
# -------------------------------
st.title(':cup_with_straw: Customize Your Smoothie! :cup_with_straw:')
st.write("Choose the fruits you want in your custom Smoothie!")

# -------------------------------
# User Input
# -------------------------------
name_on_order = st.text_input('Name on smoothie:')
st.write('The name on your smoothie will be:', name_on_order)

# -------------------------------
# Snowflake Connection
# -------------------------------
cnx = st.connection("snowflake")
session = cnx.session()

# -------------------------------
# Load Data from Snowflake
# -------------------------------
my_dataframe = session.table("smoothies.public.fruit_options") \
    .select(col('FRUIT_NAME'), col('SEARCH_ON'))

# Convert to Pandas
pd_df = my_dataframe.to_pandas()

# Optional: Show dataframe for debugging
# st.dataframe(pd_df)

# -------------------------------
# Multiselect (IMPORTANT FIX)
# -------------------------------
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    pd_df['FRUIT_NAME'],
    max_selections=5
)

# -------------------------------
# Process Selection
# -------------------------------
if ingredients_list:

    ingredients_string = ''

    for fruit_chosen in ingredients_list:

        # Build ingredients string
        ingredients_string += fruit_chosen + ' '

        # Get SEARCH_ON value
        search_on = pd_df.loc[
            pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'
        ].iloc[0]

        # Optional: ensure lowercase for API
        search_on = str(search_on).lower()

        st.write('The search value for', fruit_chosen, 'is', search_on)

        # -------------------------------
        # API Call
        # -------------------------------
        st.subheader(f"{fruit_chosen} Nutrition Information")

        try:
            response = requests.get(
                f"https://fruityvice.com/api/fruit/{search_on}"
            )

            if response.status_code == 200:
                st.write(response.json())
            else:
                st.error(f"API error for {fruit_chosen}")

        except Exception as e:
            st.error(f"Error fetching data: {e}")

    # -------------------------------
    # Insert into Snowflake (SAFE)
    # -------------------------------
    if name_on_order:
        time_to_insert = st.button('Submit Order')

        if time_to_insert:
            try:
                session.sql(
                    "INSERT INTO smoothies.public.orders (ingredients, name_on_order) VALUES (?, ?)",
                    params=[ingredients_string.strip(), name_on_order]
                ).collect()

                st.success('Your Smoothie is ordered!', icon='✅')

            except Exception as e:
                st.error(f"Insert failed: {e}")
    else:
        st.warning("Please enter your name before submitting.")
