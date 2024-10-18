import streamlit as st
import pickle
import requests
import os

# Load movie data and similarity matrix
movies = pickle.load(open("movies_list.pkl", 'rb'))
similarity = pickle.load(open("similarity.pkl", 'rb'))

# List of movie titles
movies_list = movies['title'].values

@st.cache_data(show_spinner=False)
def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=078dd0cf2fe7278cb4e016a9947d4e35&language=en-US"
    data = requests.get(url).json()
    poster_path = data.get('poster_path')
    genres = [genre['name'] for genre in data.get('genres', [])]
    overview = data.get('overview', "No overview available")
    release_date = data.get('release_date', "No release date available")
    vote_average = data.get('vote_average', "No rating available")

    if poster_path:
        full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
    else:
        full_path = "https://via.placeholder.com/500x750?text=No+Image"

    release_year = release_date.split('-')[0] if release_date != "No release date available" else "N/A"

    return full_path, genres, overview, release_year, vote_average

# Home page (Netflix-style suggestion)
def home_page():
    st.title("Discover New Movies and Series")
    st.write("Browse through our collection of movies and series.")

    # Suggest random movies
    st.subheader("Trending Now")
    trending_movies = movies.sample(10)  # Example: select 10 random movies

    cols = st.columns(5)  # Display 5 movies in a row
    for i in range(len(trending_movies)):
        movie_id = trending_movies.iloc[i].id
        movie_title = trending_movies.iloc[i].title
        poster, _, _, _, _ = fetch_movie_details(movie_id)
        
        with cols[i % 5]:
            st.image(poster, use_column_width=True)
            st.write(movie_title)

# Movie recommender page
def recommender_page():
    st.header("Movie Recommender System")
    selectvalue = st.selectbox("Select a movie from the dropdown", movies_list)

    st.subheader("Filter by Release Year")
    years = [str(year) for year in range(1990, 2023)]
    year_from = st.selectbox("From Year:", ["Any"] + years)
    year_to = st.selectbox("To Year:", ["Any"] + years)

    show_genre = st.checkbox("Show Genre")
    show_release_year = st.checkbox("Show Date")
    show_rating = st.checkbox("Show Rating")
    show_overview = st.checkbox("Show Overview")

    def round_rating(rating):
        try:
            return round(float(rating), 1)
        except ValueError:
            return "N/A"

    def recommend(movie):
        index = movies[movies['title'] == movie].index[0]
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda vector: vector[1])
        
        recommended_movies = []
        recommended_posters = []
        recommended_genres = []
        recommended_overviews = []
        recommended_release_years = []
        recommended_ratings = []

        # Change the range from 5 to 10 to get more recommendations
        for i in distances[0:10]:  # Now recommending 10 movies
            movie_id = movies.iloc[i[0]].id
            movie_title = movies.iloc[i[0]].title
            poster, genres, overview, release_year, rating = fetch_movie_details(movie_id)
            
            if release_year != "N/A":
                release_year = int(release_year)

                if ((year_from == "Any" or release_year >= int(year_from)) and
                    (year_to == "Any" or release_year <= int(year_to))):
                    recommended_movies.append(movie_title)
                    recommended_posters.append(poster)
                    recommended_genres.append(genres)
                    recommended_overviews.append(overview)
                    recommended_release_years.append(release_year)
                    recommended_ratings.append(round_rating(rating))

        return (recommended_movies, recommended_posters, recommended_genres, 
                recommended_overviews, recommended_release_years, recommended_ratings)

    def load_favorites():
        if os.path.exists("favorites.txt"):
            with open("favorites.txt", "r") as f:
                return [line.strip() for line in f.readlines()]
        return []

    def save_favorites(favorite_movies):
        with open("favorites.txt", "w") as f:
            for movie in favorite_movies:
                f.write(movie + "\n")

    def add_to_favorites(movie):
        favorites = load_favorites()
        if movie not in favorites:
            favorites.append(movie)
            save_favorites(favorites)
            return True  # Added successfully
        return False  # Already exists

    def remove_from_favorites(movie):
        favorites = load_favorites()
        if movie in favorites:
            favorites.remove(movie)
            save_favorites(favorites)
            return True  # Removed successfully
        return False  # Not found

    movie_names, movie_posters, movie_genres, movie_overviews, movie_release_years, movie_ratings = recommend(selectvalue)

    cols = st.columns(5)

    for i in range(len(movie_names)):
        with cols[i % 5]:
            with st.container():
                st.text(movie_names[i])
                st.image(movie_posters[i], use_column_width=True)

                if show_genre:
                    st.text("Genres: " + ", ".join(movie_genres[i]))

                if show_release_year:
                    st.text("Date: " + str(movie_release_years[i]))

                if show_rating:
                    st.text("Rating: " + str(movie_ratings[i]))

                if show_overview:
                    st.text("Overview: " + movie_overviews[i])

                # Add to Favorites button
                if st.button("Add to Favorites", key=f"add_{i}"):
                    if add_to_favorites(movie_names[i]):
                        st.success(f"{movie_names[i]} added to favorites!")
                    else:
                        st.warning(f"{movie_names[i]} is already in favorites!")

                # Remove from Favorites button
                if st.button("Remove from Favorites", key=f"remove_{i}"):
                    if remove_from_favorites(movie_names[i]):
                        st.success(f"{movie_names[i]} removed from favorites!")
                    else:
                        st.warning(f"{movie_names[i]} is not in favorites.")

    st.subheader("Favorites")
    favorite_movies = load_favorites()
    if favorite_movies:
        for movie in favorite_movies:
            st.text(movie)
    else:
        st.text("No favorites saved.")

# Main section to switch between pages
page = st.sidebar.selectbox("Select Page", ["Home", "Movie Recommender"])

if page == "Home":
    home_page()
else:
    recommender_page()
