import streamlit as st
import requests
from snowflake.snowpark.functions import col

st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Nombre del pedido
name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)

# Conexión con Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Cargar las opciones de frutas
fruit_rows = (
    session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS")
    .select(col("FRUIT_NAME"))
    .collect()
)
fruit_names = [row["FRUIT_NAME"] for row in fruit_rows]

# Seleccionar hasta cinco ingredientes
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_names,
    max_selections=5
)

# Construir la lista de ingredientes y mostrar SmoothieFroot
ingredients_string = ""

if ingredients_list:
    st.subheader("SmoothieFroot nutrition information")

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + " "
        st.subheader(fruit_chisen +' Nutrition Informatio')

        try:
            smoothiefroot_response = requests.get(
                "https://my.smoothiefroot.com/api/fruit/" + fruit_chosen)
               sf_df = st.datafram(data=smoothiefroot_responde.json(), use_container_width=True)

        except requests.HTTPError as error:
            response = error.response
            if response is not None:
                st.error(
                    f"SmoothieFroot returned HTTP "
                    f"{response.status_code}: {response.text[:300]}"
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
            params=[ingredients_string.strip(), name_on_order.strip()]
        ).collect()

        st.success(
            f"Your Smoothie is ordered, {name_on_order.strip()}!",
            icon="✅"
        )
