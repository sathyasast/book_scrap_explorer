import requests
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from streamlit_js_eval import streamlit_js_eval


def title_colour():
    title_color_css = """
    <style>
    h1 {
        color: #ff6347; /* Change this to your desired color */
    }
    </style>
    """
    st.markdown(title_color_css, unsafe_allow_html=True)

# Function to extract necessary fields from booksapi
def extract_fields(data,query) :
    table = []
    for i in data:
        extract_fields = {"book_id" :i["id"],
                          "search_key" : query,
                          "book_title" : i["volumeInfo"]["title"],
                          "book_subtitle" : i["volumeInfo"].get("subtitle", "NA"),
                         # "book_authors": i["volumeInfo"].get("authors", ["NA"]) if isinstance(i["volumeInfo"].get("authors"), list) else [i["volumeInfo"].get("authors", "NA")],
                          "book_authors" : ",".join(i["volumeInfo"].get("authors", [])),
                          "book_description" : i["volumeInfo"].get("description", "NA"),
                          "industryIdentifiers" : i["volumeInfo"].get("industryIdentifiers",[])[0].get("type","NA") if i["volumeInfo"].get("industryIdentifiers",[]) else "NA",
                          "text_readingModes" : i["volumeInfo"].get("readingModes","NA").get("text","NA"),
                          "image_readingModes" : i["volumeInfo"].get("readingModes","NA").get("image","NA"),
                          "pageCount" : i["volumeInfo"].get("pageCount",0),
                          "categories" : ", ".join(i["volumeInfo"].get("categories", ["NA"])),
                          "book_language" : i["volumeInfo"].get("language","NA"),
                          "imageLinks" : i["volumeInfo"].get("imageLinks",{}).get("smallThumbnail",i["volumeInfo"].get("imageLinks", {}).get("thumbnail", "NA")),
                          "ratingsCount" : i["volumeInfo"].get("ratingsCount", 0),
                          "averageRating" : i["volumeInfo"].get("averageRating",0),
                          "country" : i["saleInfo"].get("country", "NA"),
                          "saleability" : i["saleInfo"].get("saleability", "NA"),
                          "isEbook" : i["saleInfo"].get("isEbook", "NA"),
                          "amount_listPrice" : i["saleInfo"].get("listPrice",0).get("amount",0) if i["saleInfo"].get("listPrice",[]) else 0 ,
                          "currencyCode_listPrice" : i["saleInfo"].get("listPrice", "NA").get("currencyCode","NA") if i["saleInfo"].get("listPrice",[]) else "NA" ,
                          "amount_retailPrice" : i["saleInfo"].get("retailPrice", 0).get("amount",0) if i["saleInfo"].get("retailPrice",[]) else 0,
                          "currencyCode_retailPrice" : i["saleInfo"].get("retailPrice", "NA").get("currencyCode","NA")if i["saleInfo"].get("retailPrice",[]) else "NA",
                          "buyLink" : i["saleInfo"].get("buyLink", "NA"),
                          "publish_year" : i["volumeInfo"].get("publishedDate","NA"),
                          "publisher" : i["volumeInfo"].get("publisher","NA")
                         }
        table.append(extract_fields)
        #columns = list(extract_fields.keys())
    return table

# Defining a scrapper to fetch data from booksapi
def scrap(query,count):
    url = "https://www.googleapis.com/books/v1/volumes"
    api_key = "AIzaSyB245M5jwzfHJkhs78bQUM2Faw29Nqz8X0"
    all_books = []
    i = 0
    try:
        while len(all_books)<count:  # Handling pagination
            response = requests.get(url, params = {"q" : query, "key" : api_key, "startIndex" : i, "maxResults" : 40})
            if response.status_code == 200 :
                data = response.json()
                items = data.get("items",[])
                if not items:
                    print("No more books found")
                    break
                all_books.extend(items)
                i += 40  # incrementing the index value to handle pagination
                if len(items)< 40 :
                    break
    except requests.exceptions.RequestException as e:
        st.error(e)
    required_data = extract_fields(all_books[:int(count)],query)
    
    return required_data

# Defined a Function to establish connection with mysql db using sqlalchemy package
def open_sql_connection():
    username = "root"
    password = "sathya"
    host = "localhost"
    database = "Book_Scrap"

    connection_string = f'mysql+mysqlconnector://{username}:{password}@{host}/{database}'
    engine = create_engine(connection_string)
    return engine

title_colour()

st.title("Bookscape Explorer")

# Adding button variables to session state to handle execution flow
if "Store" not in st.session_state:
    st.session_state["Store"]= False
if "Proceed" not in st.session_state:
    st.session_state["Proceed"] = False
if "DataFetched" not in st.session_state:
    st.session_state["DataFetched"] = False

# Getting user input 
category = st.text_input("Enter the category of books to be explored")
count = st.number_input("Enter the count of books to be fetched for analysis")


# Based on user input data being fetched from booksapi and displayed in the streamlit app
if category and count and not st.session_state["DataFetched"]:
    with st.spinner("Fetching data") :
        data = scrap(category,count)
        df_books = pd.DataFrame(data)
    if not df_books.empty:
        st.write(df_books)
        st.session_state["DataFetched"] = True
        df_books = df_books.drop_duplicates(subset=['book_id'])
        st.session_state["df_books"] = df_books
    else:
        st.error("No books found")

# creating store button
if st.session_state.get("DataFetched"):
    df_books = st.session_state["df_books"]
    if not df_books.empty:
        if st.button("Store"):
            st.session_state["Store"] = not st.session_state["Store"]
            df_books = df_books.drop_duplicates(subset=['book_id'])
#fetching the existing records from the db
            try:
                engine = open_sql_connection()
                connection = engine.connect()
                connection.execute(text("use Book_Scrap"))
                key = connection.execute(text("select distinct(search_key) as category, count(book_id) as record_count from books group by category"))
                key = key.fetchall()
                if key == []:
                    st.write("No records found")
                else:
                    st.write("currently the database contains the below records")
                    st.write(pd.DataFrame(key))
                    st.warning("If you still wish to continue click on proceed")
            except Exception as e:
                st.error(e)

# Creating proceed button to store the data in db
        if st.session_state["Store"]:
           if st.button("Proceed"):
                st.session_state["Proceed"] = not st.session_state["Proceed"]

        if st.session_state["Proceed"]:
            with st.spinner("Storing Data"):
                engine = open_sql_connection()
                connection = engine.connect()
# fetching already existing search_key in the db
                connection.execute(text("use Book_Scrap"))
                key = connection.execute(text("select distinct(search_key) as category, count(book_id) as record_count from books group by category"))
                key = key.fetchall()
# If the user input search_key present in db then clearing all the data corresponding to the search_key to handle duplicacy
                for x in key:
                    if category == x[0].strip():
                        connection.execute(text("delete from books where search_key = :x"),{"x":x[0].strip()})
                        connection.commit()
# Passing data to mysql db through sqlalchemy
                df_books.to_sql('books',con=engine,index=False,if_exists='append')
                st.success("Data stored successfully")
# clearing the session states
                for key in st.session_state.keys():
                    if key != "df_books":
                        del st.session_state[key]

