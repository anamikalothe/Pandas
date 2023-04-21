# -*- coding: utf-8 -*-
"""
Created on Thu Mar  2 09:33:51 2023

@author: Anamika_Lothe
"""

import pandas as pd
from forex_python.converter import CurrencyRates
import matplotlib.pyplot as plt
import json
import csv
df = pd.read_csv(r"C:\Users\Anamika_Lothe\Downloads\Movie Data.csv")


def get_movies_by_genre(n: int, genres: str):
    '''
    :param n (int): A percentage value (0-100) to filter the movies by their metascore and IMDb user votes.
    :param genres (str): A string containing the genre(s) of the movies to be filtered.
    :return:
    '''
    global df
    df = df.dropna()
    genres_data = df[df['genres'].str.contains(genres)]

    genres_data = genres_data[genres_data['metascore'] != -1]
    
    bottom_n, top_n = genres_data['metascore'].quantile([n/100, (100-n)/100])
  
    bottom_n_movie = list(genres_data[genres_data['metascore'] <= bottom_n]['title'])
    top_n_movie = list(genres_data[genres_data['metascore'] >= top_n]['title'])
    
    imdbUserVotes = df[df['number of imdb user votes'] != -1]
  
    bottom_n1, top_n1 = imdbUserVotes['number of imdb user votes'].quantile([n/100, (100-n)/100])
 
    bottom_n_movie_by_votes = list(imdbUserVotes[imdbUserVotes['number of imdb user votes'] <= bottom_n1]['title'])
    top_n_movie_by_votes = list(imdbUserVotes[imdbUserVotes['number of imdb user votes'] >= top_n1]['title'])
    
    return bottom_n_movie, top_n_movie, bottom_n_movie_by_votes, top_n_movie_by_votes

bottom_n_movie, top_n_movie, bottom_n_movie_by_votes, top_n_movie_by_votes = get_movies_by_genre(5, "Comedy")
my_tuple = bottom_n_movie, top_n_movie, bottom_n_movie_by_votes, top_n_movie_by_votes
my_list = list(my_tuple)
print(my_list)


def find_movies_with_oscar(year):
    '''
    :param year: an integer value representing the year for which the function finds Oscar-winning movies
    :return:
    '''
    oscar_winners = df[(df["awards"].str.contains("Oscar") == True) & (df["awards"].str.contains("Oscar "+ str(year)))]
    return oscar_winners["title"].tolist()


def analyze_movies_budget(n, highest=True):
    '''
    :param n: an integer that represents the number of movies to be returned
    :param highest: a boolean that determines whether to return the movies with the highest or lowest budget.
    :return:
    '''
    df['budget'] = df['budget'].str.replace('$', 'USD')

    df[['currency_symbol', 'budget_value', 'estimated']] = df['budget'].str.extract(r'^(\D*)(\d[\d,\.]*)(.*)$')

    df['budget_value'] = df['budget_value'].str.replace(',', '').astype(float)

    df.dropna(subset=['budget_value'], inplace=True)

    c = CurrencyRates()

    target_currency = 'USD'

    df['budget_value_usd'] = df.apply(lambda row: c.convert(row['currency_symbol'], target_currency, row['budget_value']), axis=1)

    df['budget_string'] = target_currency + ' ' + df['budget_value_usd'].astype(str)

    if highest:
        sorted_movies = df.sort_values(by=['budget_value_usd'], ascending=False).head(n)
    else:
        sorted_movies = df.sort_values(by=['budget_value_usd'], ascending=True).head(n)

    return sorted_movies[['title', 'budget_string']]


def top_countries_by_movie_count(df):
    '''
    :param df: pandas DataFrame containing movie data
    :return:
    '''
    df = df[df['year'] != 1]
    df = df.assign(countries=df['countries'].str.split(',')).explode('countries')
    movie_counts = df.groupby(['year', 'countries']).size().reset_index(name='count')
    top_countries = movie_counts.loc[movie_counts.groupby('year')['count'].idxmax()]
    for _, row in top_countries.iterrows():
        year = row['year']
        country = row['countries']
        count = row['count']
        print(f"{year}, {country}, {count}")
    return top_countries

'''
creates a scatter plot to explore the relationship between the IMDB user rating 
and the number of awards a movie has received.
'''
df['awards_count'] = df['awards'].str.count(',') + 1
df_filtered = df[df['imdb user rating'] != -1]
plt.scatter(df_filtered['imdb user rating'], df_filtered['awards_count'])
plt.xlabel('IMDB User Rating')
plt.ylabel('Awards Count')
plt.title('Relationship between IMDB User Rating and Awards Count')


def get_akas_for_region(movie, region):
    '''
    :param movie (str): The title of the movie to search for.
    :param region (str): The region for which the alternative titles are to be returned.
    :return:
    :raises exception: If the specified region does not have alternative titles for the specified movie.
    '''
    akas_of_movie = df.loc[df['title'] == movie, 'akas'].values[0]
    if region not in akas_of_movie:
        raise Exception("Region does not have akas")
    akas_dict = {}
    for part in akas_of_movie.split(','):
        part = part.strip()
        if f"({region}" in part:
            akas_region = part.split("(")[0].strip()
            if region in akas_dict:
                akas_dict[region].append(akas_region)
            else:
                akas_dict[region] = [akas_region]

    return akas_dict.get(region, [])


def movies_by_year(df, year, condition):
    '''
    :param df : pandas.DataFrame
        A pandas DataFrame containing movie data.
        
    :param year : int
    The year to filter the movies by.
    
    :param condition : str
        The condition to filter the movies by. Must be one of 'on', 'before', or 'after'.
    :return:
    '''
    df = df[df['year'] != 1]
    if condition == "on":
        filtered_movies = df[df["year"] == year]
    elif condition == "before":
        filtered_movies = df[df["year"] < year]
    elif condition == "after":
        filtered_movies = df[df["year"] > year]
    else:
        raise ValueError("Invalid condition. Please choose 'on', 'before', or 'after'.")
    
    output = pd.DataFrame({
        "title": filtered_movies["title"],
        "condition": condition
    })
    return output


def find_director_with_most_oscar_wins(df):
    '''
    :param df (pandas.DataFrame): The DataFrame to be analyzed. Must have columns named "awards" and "directors".
    :return:
    '''
    awards_df = df['awards'].str.split(', ', expand=True)

    df['oscar_wins'] = awards_df.apply(lambda row: 'Oscar' in row.values, axis=1)
    
    oscar_wins_by_director = df.groupby('directors')['oscar_wins'].count()

    most_oscar_wins = oscar_wins_by_director.idxmax()

    return most_oscar_wins


def write_output_to_json(function, filename, *args):
    """
    Write the output of a function to a JSON file.

    :param function (function): The function whose output is to be written to a JSON file.
    :param filename (str): The name of the JSON file to write the output to.
    *args: Variable length argument list to pass to the function.

    :raises ValueError: If the output is not in a format that can be written to a JSON file.
    """
    output = function(*args)
    if isinstance(output, (list, tuple)):
        with open(filename, 'w') as jsonfile:
            json.dump(output, jsonfile)
    elif isinstance(output, pd.DataFrame):
        output.to_json(filename)
    elif isinstance(output, str):
        with open(filename, 'w') as jsonfile:
            json.dump([output], jsonfile)
    else:
        raise ValueError("output not in format that can be written to a JSON file")

def write_output_to_csv(function, filename, *args):
    """
    Write the output of a function to a CSV file.

    :param function (function): The function whose output is to be written to a JSON file.
    :param filename (str): The name of the JSON file to write the output to.
    *args: Variable length argument list to pass to the function.

    :raises ValueError: If the output is not in a format that can be written to a JSON file.
    """
    output = function(*args)
    if isinstance(output, (list, tuple)):
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(output)
    elif isinstance(output, pd.DataFrame):
        output.to_csv(filename, index=False)
    elif isinstance(output, str):
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([output])
    else:
        raise ValueError("output not in format that can be written to a CSV file")


def main():
    '''
    Task-1
    Group movies by genres-
    a. Top/bottom n percentile movies according to metascore, where, ‘n’ should be a
    parameter passed to your function. For example, if n is 10, then you will be
    expected to find the movies above 90 percentile (top) and below 10 percentile
    (bottom) for each genre.
    b. Top/bottom n percentile movies according to ‘number of imdb user votes’
    '''
    write_output_to_json(get_movies_by_genre, 'output1.json', 10, 'Comedy')
    write_output_to_csv(get_movies_by_genre, 'output1.csv', 10, 'Comedy')

    '''
    Task-2
    Movies who have won an Oscar in a particular year. For example, get the year as a
    parameter to your function and return all the movies that won an Oscar in that year
    '''  
    write_output_to_json(find_movies_with_oscar, 'output2.json', 2010)
    write_output_to_csv(find_movies_with_oscar, 'output2.csv', 2010)

    '''
    Task-3
    Analyze and return n movies with highest/lowest budget
    '''
    write_output_to_json(analyze_movies_budget, 'output3.json', 5, 'highest=True')
    write_output_to_csv(analyze_movies_budget, 'output3.csv', 5, 'highest=True')

    '''
    Task-4
    Which countries have highest number of movies release in each year
    '''
    write_output_to_json(top_countries_by_movie_count, 'output4.json', df)
    write_output_to_csv(top_countries_by_movie_count, 'output4.csv', df)
    
    '''
    Task-5
    Analyze if there is any relationship between the imdb user rating and number of awards received
    '''
    plt.savefig("user-rating vs awards-count.png")
    
    '''
    Task-6
    Return akas of a specified movie in a specified region
    '''
    write_output_to_json(get_akas_for_region, 'output6.json', "The Transformers: The Movie", "Japan")
    write_output_to_csv(get_akas_for_region, 'output6.csv', "The Transformers: The Movie", "Japan")

    '''
    Task-7
    Movies released on, before or after a given year (take year as a parameter)
    '''
    write_output_to_json(movies_by_year, 'output7.json', df, 1913, 'before')
    write_output_to_csv(movies_by_year, 'output7.csv', df, 2021, 'on')

    '''
    Task-8
    Which director has made directed most number of oscar winning movies
    '''
    write_output_to_json(find_director_with_most_oscar_wins, 'output8.json', df)
    write_output_to_csv(find_director_with_most_oscar_wins, 'output8.csv', df)
    
if __name__ == '__main__':
    main()
