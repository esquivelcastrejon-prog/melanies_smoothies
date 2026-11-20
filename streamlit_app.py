import streamlit as st
from snowflake.snowpark.functions import col

st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)

# Conexión con Snowflake configurada en Streamlit Secrets
cnx = st.connection("snowflake")
session = cnx.session()

# Cargar las opciones de frutas
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
