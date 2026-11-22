import streamlit as st
import requests
import pandas as pd
from urllib.parse import quote
from snowflake.snowpark.functions import col

st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Nombre del pedido
name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)

# Conexión con Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Cargar FRUIT_NAME y SEARCH_ON desde Snowflake
my_dataframe = (
    session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS")
    .select(col("FRUIT_NAME"), col("SEARCH_ON"))
)

# Convertir el DataFrame de Snowpark a pandas
pd_df = pd.DataFrame(my_dataframe.to_pandas())

# Para revisar temporalmente las dos columnas, descomenta esta línea:
# st.dataframe(pd_df, width="stretch")

# Alimentar el selector con los nombres visibles
fruit_names = pd_df["FRUIT_NAME"].tolist()

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_names,
    max_selections=5
)

# Consultar SmoothieFroot usando el valor SEARCH_ON
ingredients_string = " ".join(ingredients_list)

if ingredients_list:
    for fruit_chosen in ingredients_list:
        search_values = pd_df.loc[
            pd_df["FRUIT_NAME"] == fruit_chosen,
            "SEARCH_ON"
        ]

        if search_values.empty or pd.isna(search_values.iloc[0]):
            st.warning(f"No SEARCH_ON value is set for {fruit_chosen}.")
            continue

        search_on = str(search_values.iloc[0]).strip()

        st.write(f"The search value for {fruit_chosen} is {search_on}.")
        st.subheader(f"{fruit_chosen} Nutrition Information")

        try:
            fruit_path = quote(search_on, safe="")
            response = requests.get(
                f"https://my.smoothiefroot.com/api/fruit/{fruit_path}",
                headers={"Accept": "application/json"},
                timeout=15
            )
            response.raise_for_status()

            st.dataframe(
                data=response.json(),
                width="stretch"
            )

        except requests.HTTPError as error:
            api_response = error.response
            if api_response is not None:
                st.error(
                    f"SmoothieFroot returned HTTP "
                    f"{api_response.status_code}: "
                    f"{api_response.text[:300]}"
                )
            else:
                st.error(f"Could not retrieve SmoothieFroot data: {error}")

        except requests.RequestException as error:
            st.error(f"Could not retrieve SmoothieFroot data: {error}")

        except ValueError:
            st.error("SmoothieFroot returned a response that is not valid JSON.")

# Registrar el pedido
if st.button("Submit Order"):
    if not name_on_order.strip():
        st.warning("Please enter a name for the order.")
    elif not ingredients_list:
        st.warning("Please choose at least one ingredient.")
    else:
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
