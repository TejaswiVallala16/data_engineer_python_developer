import pandas as pd
import streamlit as st
import altair as alt

# Load cleaned data
df = pd.read_csv("books_scrapper/books.csv")

# Sidebar filters
st.sidebar.header("Filters")
categories = st.sidebar.multiselect(
    "Select categories", options=df["category"].unique(), default=df["category"].unique()
)

# Filtered dataframe
df_filtered = df[df["category"].isin(categories)]

# Title
st.title("Book Price Trends Dashboard")

st.markdown("### Average Price per Category")

avg_price = df_filtered.groupby("category")["price"].mean().reset_index()

chart = (
    alt.Chart(avg_price)
    .mark_bar()
    .encode(
        x=alt.X("category:N", sort="-y"),
        y="price:Q",
        tooltip=["category", "price"]
    )
    .properties(height=400)
)
st.altair_chart(chart, use_container_width=True)

# Show top expensive books
st.markdown("### Top 10 Most Expensive Books")
top_books = df_filtered.nlargest(10, "price")[["title", "category", "price"]]
st.table(top_books)


# Scatter plot price vs rating
st.markdown("### Price vs Rating")
scatter = (
    alt.Chart(df_filtered)
    .mark_circle(size=60)
    .encode(
        x="rating:Q",
        y="price:Q",
        color="category:N",
        tooltip=["title", "price", "rating", "category"]
    )
    .interactive()
)
st.altair_chart(scatter, use_container_width=True)