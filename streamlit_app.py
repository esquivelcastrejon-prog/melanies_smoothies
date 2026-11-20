import streamlit as st
from snowflake.snowpark.context import get_active_session

# Título y texto de la app
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Nombre del pedido
name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)

# Conexión y opciones de frutas
session = get_active_session()

fruit_rows = (
    session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS")
    .select("FRUIT_NAME")
    .collect()
)
fruit_names = [row["FRUIT_NAME"] for row in fruit_rows]

# Selección de ingredientes
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_names,
    max_selections=5
)

if ingredients_list:
    ingredients_string = " ".join(ingredients_list).strip()

    # Escapar apóstrofes para que el texto no rompa el SQL
    ingredients_sql = ingredients_string.replace("'", "''")
    name_sql = name_on_order.strip().replace("'", "''")

    # INSERT con las dos columnas y sus dos valores
    my_insert_stmt = (
        "INSERT INTO SMOOTHIES.PUBLIC.ORDERS "
        "(INGREDIENTS, NAME_ON_ORDER) "
        f"VALUES ('{ingredients_sql}', '{name_sql}')"
    )

    # Para comprobar el SQL en una Worksheet, descomenta estas dos líneas.
    # Después de validarlo, vuelve a comentarlas para usar el botón.
    # st.write(my_insert_stmt)
    # st.stop()

    if st.button("Submit Order"):
        session.sql(my_insert_stmt).collect()
        st.success(
            f"Your Smoothie is ordered, {name_on_order.strip()}!",
            icon="✅"
        )
