import streamlit as st

# Setting page configuration
def page_config() :
    st.set_page_config(
        page_title = "Bookscape explorer",
    )

# styling the title
def title_colour():
    title_color_css = """
    <style>
    h1 {
        color: #ff6347; /* Change this to your desired color */
    }
    </style>
    """
    st.markdown(title_color_css, unsafe_allow_html=True)


page_config()
title_colour()


#components to be displayed in the home page
st.title("Data analysis with Google booksapi")

st.write("This application allows you to scrap required data from Google books shelf using booksapi and store it in your local database for future analysis")

st.image(f"G:\guvi\chart.jpg")


