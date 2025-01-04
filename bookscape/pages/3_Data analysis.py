import streamlit as st
from sqlalchemy import create_engine,text
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
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



title_colour()



st.title("Data Analysis")

# Storing all the queries in a dictionary format

queries = {"Check Availability of eBooks vs Physical Books ":"""select case when isEbook = 1 then "ebook" else "physical book" end as book_type, count(*) as total_books, sum(case when saleability = "FOR_SALE" then 1 else 0 end) as availability from books group by isEbook""",
           "Find the Publisher with the Most Books Published" : """select publisher, count(book_id) as count from books group by publisher having publisher != "NA" order by count desc limit 1""",
           "Identify the Publisher with the Highest Average Rating":"""select publisher, averageRating from books where averageRating = 5""",
           "Get the Top 5 Most Expensive Books by Retail Price" : """select book_title as books , amount_retailPrice from books order by amount_retailPrice desc limit 5""",
           "Find Books Published After 2010 with at Least 500 Pages":"""select book_title , publish_year, pageCount from books where publish_year > 2010 and pageCount > 500""",
           "List Books with Discounts Greater than 20%" : """select book_title , ((amount_listPrice - amount_retailPrice)/amount_listPrice) * 100 as discount_percentage from books having discount_percentage> 20""",
           "Find the Average Page Count for eBooks vs Physical Books":"""select case when isEbook = 0 then "physical_book" else "ebook" end as book_type, avg(pageCount) as avg_page_count from books group by isEbook""",
           "Find the Top 3 Authors with the Most Books": """select book_authors , count(book_id)as book_count from books group by book_authors order by book_count desc limit 3""",
           "List Publishers with More than 10 Books": """select publisher, count(book_id) as book_count from books group by publisher having book_count > 10""",
           "Find the Average Page Count for Each Category":"""select categories, avg(pageCount) as page_count from books group by categories having categories != "NA""",
           "Retrieve Books with More than 3 Authors" : """SELECT book_title, length(book_authors) - LENGTH(REPLACE(book_authors, ',', '')) + 1 as author_count FROM books WHERE LENGTH(book_authors) - LENGTH(REPLACE(book_authors, ',', '')) + 1 > 3""",
           "Books with Ratings Count Greater Than the Average": """select book_title, ratingsCount from books where ratingsCount > averageRating""",
           "Books with the Same Author Published in the Same Year":"""select book_title, book_authors, publish_year from books where(book_authors, publish_year) IN ( select book_authors, publish_year from books group by book_authors, publish_year having count(*)>1) order by book_authors, publish_year""",
           "Year with the Highest Average Book Price" : """select substring(publish_year,1,4)as year, avg(amount_retailPrice) as avg_price from books group by publish_year order by avg_price desc limit 1""",
           "Count Authors Who Published 3 Consecutive Years":"""with extractyear as (
select book_authors, cast(substring(publish_year,1,4) as unsigned) as year,
lead(cast(substring(publish_year,1,4) as unsigned)) over (partition by book_authors order by cast(substring(publish_year,1,4) as unsigned)) as next_year,
lag(cast(substring(publish_year,1,4) as unsigned)) over (partition by book_authors order by cast(substring(publish_year,1,4) as unsigned)) as prev_year 
from books ),
consecutiveyears as (
select distinct(book_authors) from extractyear where year = prev_year + 1 and year = next_year - 1)
select count(*) as author_count from consecutiveyears""",
"Authors who have published books in the same year but under different publishers" : """select book_authors, cast(substring(publish_year,1,4) as unsigned) as year, count(*) as book_count from books group by book_authors, year having count(distinct publisher) > 1""",
"Find the average amount_retailPrice of eBooks and physical books" : """select ifnull(avg(case when isEbook = 0 then amount_listPrice end),0) as avg_physical_price, ifnull(avg(case when isEbook = 1 then amount_listPrice end),0) as avg_ebook_price  from books""",
"Identify books that have an averageRating that is more than two standard deviations away from the average rating of all books":"""with stats as (
select avg(averageRating) as avg_rating , stddev(averageRating) as std_rating from books
)
select book_title, averageRating, ratingsCount from books, stats where averageRating > ( avg_rating + 2* std_rating) or averageRating < (avg_rating - 2*std_rating)""",
"Which publisher has the highest average rating among its books, but only for publishers that have published more than 10 books": """SELECT 
    publisher, 
    avg_rating, 
    book_count, 
    ranks
FROM (
    SELECT 
        publisher, 
        MAX(averageRating) AS avg_rating, 
        COUNT(*) AS book_count, 
        RANK() OVER (ORDER BY MAX(averageRating) DESC) AS ranks
    FROM books 
    WHERE publisher IN (
        SELECT publisher 
        FROM books 
        GROUP BY publisher 
        HAVING COUNT(book_id) > 10
    ) 
    GROUP BY publisher
) AS ranked_publishers
WHERE ranks = 1"""
           }

# creating a sidebar with selectbox for choosing query
st.sidebar.title("Query the Data")

option = st.sidebar.selectbox("Choose a query for analysis",list(queries.keys()),index=None)

def open_sql_connection():
    username = "root"
    password = "sathya"
    host = "localhost"
    database = "Book_Scrap"

    connection_string = f'mysql+mysqlconnector://{username}:{password}@{host}/{database}'
    engine = create_engine(connection_string)
    return engine

# created a function to generate charts
def generate_visualisation(choice,df):
    flag = 0
    #Line chart
    if choice in ["Get the Top 5 Most Expensive Books by Retail Price","List Publishers with More than 10 Books"]:
        flag = 1
        st.write(choice)
        df_sorted = df.sort_values(by=df.columns[1])
        fig = px.line(
        df_sorted,
        x=df_sorted.columns[0],  # X-axis
        y=df_sorted.columns[1],  # Y-axis
        title="Line Chart with Correct Y-Axis"
        )   


        fig.update_layout(
        yaxis=dict(autorange=True)  # Forces ascending order for y-axis
        )

        st.plotly_chart(fig)
    #Bar chart
    elif choice in ["Retrieve Books with More than 3 Authors"]:
        flag = 1
        st.write(choice)
        st.bar_chart(df,x=df.columns[0],y=df.columns[1])
    # Horizontal bars
    elif choice in ["Find the Average Page Count for eBooks vs Physical Books","Find the average amount_retailPrice of eBooks and physical books"]:
        flag = 1
        fig = go.Figure(
            data=[go.Bar(
                x=list(df[df.columns[1]]),
                y=list(df[df.columns[0]]),
                orientation = 'h',
                marker=dict(color='blue'),
                text=list(df[df.columns[1]]),
                textposition = 'auto'
            )]
        )

        fig.update_layout(
            title=choice,
            xaxis=dict(
                showline=False,
                showticklabels=False,
                ticks="",
            ),
            yaxis=dict(
                showline=False,
                ticks="",
            ),
            template="simple_white",
            
        )
        st.plotly_chart(fig)
    # Pie chart   
    elif choice in ["Find the Top 3 Authors with the Most Books","Find the Average Page Count for Each Category"]:
        flag = 1
        df=df[df[df.columns[1]]>0]
        fig,ax = plt.subplots()
        ax.pie(df[df.columns[1]], labels= df[df.columns[0]], autopct="%1.1f%%",labeldistance=1.2)
        ax.axis('equal')
        plt.tight_layout()
        st.pyplot(fig)

    return flag
    


if option != None:
    engine = open_sql_connection()
    connection = engine.connect()
    connection.execute(text("use Book_Scrap"))

    if 'data' not in st.session_state:
        st.session_state.data=[]

# adding to selected query and it's result to session state for creating dynamic layouts
    if option not in [data['name'] for data in st.session_state.data]:
        result = connection.execute(text(queries[option]))
        result = result.fetchall()
        df = pd.DataFrame(result)
        if df.empty:
            st.warning("No data found for this query")
        else:
            #st.write(df)
            st.session_state.data.append({'name': option, 'output' : df})

    rm_items = []
# defining layout like 2x2 grid, charts are displayed in a split column fashion
    if len(st.session_state.data)>0:
        grid_cols = 2
        for i in range(0,len(st.session_state.data),grid_cols):
            col1, col2 = st.columns(2)
            for j, col in enumerate([col1,col2]):
                idx = i+j
                if idx < len(st.session_state.data):
                    result = st.session_state.data[idx]
                    with col:
                        flag = 0
                        flag = generate_visualisation(result['name'],result['output'])
                        if flag == 0:
                            st.write(result['name'])
                            st.write(result['output'])
# Adding a checkbox called remove against each chart
                        remove = st.checkbox(f"Remove",key=f'{result["name"]}')
                        if remove:
                            rm_items.append(result)
                            # st.session_state.data=[r for r in st.session_state.data if r != result]
                                # st.rerun()
# A button called clear is created to remove all the checked charts from the display
    if st.button("Clear"):
        st.session_state.data = [item for item in st.session_state.data if item not in rm_items]
        st.rerun()
# A reset all button is created to remove all the visualisation in single go
    if st.button("Reset all"):
        rm_items.clear()
        st.session_state.data=[]
        streamlit_js_eval(js_expressions="parent.window.location.reload()")


    

