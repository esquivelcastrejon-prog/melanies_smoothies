import streamlit as st
import requests
from snowflake.snowpark.functions import col

st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Nombre del pedido
name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)

# Conexión con Snowflake configurada en Streamlit Secrets
cnx = st.connection("snowflake")
session = cnx.session()

# Cargar las opciones de frutas desde Snowflake
fruit_rows = (
    session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS")
    .select(col("FRUIT_NAME"))
    .collect()
)
fruit_names = [row["FRUIT_NAME"] for row in fruit_rows]

# Selección de hasta cinco ingredientes
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_names,
    max_selections=5
)

# Registrar el pedido
if st.button("Submit Order"):
    if not name_on_order.strip():
        st.warning("Please enter a name for the order.")
    elif not ingredients_list:
        st.warning("Please choose at least one ingredient.")
    else:
        ingredients_string = " ".join(ingredients_list)

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

# Consultar y mostrar información de la sandía desde SmoothieFroot
st.subheader("Watermelon nutrition information")

try:
    smoothiefruit_response = requests.get(
        "https://my.smoothiefroot.com/api/fruit/watermelon",
        timeout=15
    )
    smoothiefruit_response.raise_for_status()
    smoothiefruit_data = smoothiefruit_response.json()

    st.dataframe([smoothiefruit_data], use_container_width=True)

except requests.RequestException as error:
    st.error(f"Could not retrieve information from SmoothieFroot: {error}")

except ValueError:
    st.error("SmoothieFroot returned a response that is not valid JSON.")
