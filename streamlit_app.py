import streamlit as st
import requests
import pandas as pd
from urllib.parse import quote
from snowflake.snowpark.functions import col

st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)

# Conexión con Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Cargar el nombre visible y el término de búsqueda de la API
my_dataframe = (
    session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS")
    .select(col("FRUIT_NAME"), col("SEARCH_ON"))
)

# Convertir Snowpark DataFrame a pandas para buscar con .loc
pd_df = my_dataframe.to_pandas()

fruit_names = (
    pd_df["FRUIT_NAME"]
    .dropna()
    .astype(str)
    .tolist()
)

# Seleccionar hasta cinco ingredientes
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_names,
    max_selections=5
)

# Mostrar información nutricional de las frutas elegidas
if ingredients_list:
    for fruit_chosen in ingredients_list:
        st.subheader(f"{fruit_chosen} Nutrition Information")

        matches = pd_df.loc[
            pd_df["FRUIT_NAME"] == fruit_chosen,
            "SEARCH_ON"
        ]

        if matches.empty or pd.isna(matches.iloc[0]):
            st.warning(
                f"No SEARCH_ON value is configured for {fruit_chosen} "
                "in FRUIT_OPTIONS."
            )
            continue

        search_on = str(matches.iloc[0]).strip()

        if not search_on:
            st.warning(f"The SEARCH_ON value for {fruit_chosen} is empty.")
            continue

        # Codificar el término por si contiene espacios o paréntesis
        fruit_path = quote(search_on, safe="")

        try:
            response = requests.get(
                f"https://my.smoothiefroot.com/api/fruit/{fruit_path}",
                headers={"Accept": "application/json"},
                timeout=15
            )
            response.raise_for_status()

            fruit_data = response.json()
            fruit_df = pd.json_normalize(fruit_data, sep=".")

            if fruit_df.empty:
                st.info(f"No nutrition data was returned for {fruit_chosen}.")
            else:
                st.dataframe(
                    fruit_df,
                    width="stretch",
                    hide_index=True
                )

        except requests.HTTPError as error:
            error_response = error.response

            if error_response is not None:
                st.error(
                    f"SmoothieFroot returned HTTP "
                    f"{error_response.status_code}: "
                    f"{error_response.text[:300]}"
                )
            else:
                st.error(f"Could not retrieve SmoothieFroot data: {error}")

        except requests.RequestException as error:
            st.error(f"Could not retrieve SmoothieFroot data: {error}")

        except (ValueError, TypeError) as error:
            st.error(
                f"Could not read SmoothieFroot's JSON response: {error}"
            )

# Registrar el pedido
if st.button("Submit Order"):
    if not name_on_order.strip():
        st.warning("Please enter a name for the order.")
    elif not ingredients_list:
        st.warning("Please choose at least one ingredient.")
    else:
        # El espacio final es necesario para el check del taller.
        # El orden de los ingredientes también debe conservarse.
        ingredients_string = "".join(
            f"{fruit} " for fruit in ingredients_list
        )

        insert_stmt = """
            INSERT INTO SMOOTHIES.PUBLIC.ORDERS
                (INGREDIENTS, NAME_ON_ORDER)
            VALUES (?, ?)
        """

        session.sql(
            insert_stmt,
            params=[ingredients_string, name_on_order.strip()]
        ).collect()

        st.success(
            f"Your Smoothie is ordered, {name_on_order.strip()}!",
            icon="✅"
        )
