import os
import json
import time
import requests
from collections import Counter
from datetime import datetime


TMDB_TOKEN = os.environ["TMDB_TOKEN"]

BASE_URL = "https://api.themoviedb.org/3"

HEADERS = {
    "Authorization": f"Bearer {TMDB_TOKEN}",
    "accept": "application/json"
}


# =========================
# TMDB REQUEST
# =========================

def tmdb_get(endpoint, params=None):

    url = BASE_URL + endpoint

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# =========================
# GENRES
# =========================

GENRES = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Family",
    14: "Fantasy",
    36: "History",
    27: "Horror",
    10402: "Music",
    9648: "Mystery",
    10749: "Romance",
    878: "Science Fiction",
    10770: "TV Movie",
    53: "Thriller",
    10752: "War",
    37: "Western"
}


# =========================
# GET TOP ACTORS
# =========================

def get_popular_actors():

    actors = []
    seen_ids = set()

    page = 1

    while len(actors) < 1000 and page <= 500:

        print(f"Getting popular people page {page}...")

        data = tmdb_get(
            "/person/popular",
            {
                "language": "en-US",
                "page": page
            }
        )

        for person in data.get("results", []):

            person_id = person.get("id")

            if person_id in seen_ids:
                continue

            if person.get("adult"):
                continue

            if person.get("known_for_department") != "Acting":
                continue

            if not person.get("profile_path"):
                continue

            if person.get("gender") not in [1, 2]:
                continue

            seen_ids.add(person_id)

            actors.append(person)

            if len(actors) >= 1000:
                break

        page += 1

        time.sleep(0.05)

    return actors


# =========================
# GET PERSON DATA
# =========================

def get_person_data(person_id):

    details = tmdb_get(
        f"/person/{person_id}",
        {
            "language": "en-US"
        }
    )

    time.sleep(0.05)

    credits = tmdb_get(
        f"/person/{person_id}/combined_credits",
        {
            "language": "en-US"
        }
    )

    time.sleep(0.05)

    return details, credits


# =========================
# BIRTH YEAR
# =========================

def get_birth_year(details):

    birthday = details.get("birthday")

    if not birthday:
        return None

    try:
        return int(birthday[:4])
    except:
        return None


# =========================
# GENDER
# =========================

def get_gender(details):

    gender = details.get("gender")

    if gender == 1:
        return "Female"

    if gender == 2:
        return "Male"

    return "Unknown"


# =========================
# MOST ACTED GENRE
# =========================

def get_main_genre(credits):

    counter = Counter()

    for credit in credits.get("cast", []):

        genres = credit.get("genre_ids", [])

        for genre_id in genres:

            if genre_id in GENRES:
                counter[GENRES[genre_id]] += 1

    if not counter:
        return "Unknown"

    return counter.most_common(1)[0][0]


# =========================
# BREAKOUT YEAR
# =========================

def get_breakout_year(credits):

    best_credit = None
    best_score = -1

    for credit in credits.get("cast", []):

        date = (
            credit.get("release_date")
            or credit.get("first_air_date")
        )

        if not date:
            continue

        try:
            year = int(date[:4])
        except:
            continue

        popularity = credit.get("popularity", 0)

        if popularity > best_score:

            best_score = popularity

            best_credit = year

    return best_credit


# =========================
# NATIONALITY
# =========================

def get_nationality(details):

    place = details.get("place_of_birth")

    if not place:
        return "Unknown"

    place = place.lower()

    countries = {
        "united states": "American",
        "usa": "American",
        "england": "British",
        "london": "British",
        "scotland": "Scottish",
        "wales": "Welsh",
        "ireland": "Irish",
        "australia": "Australian",
        "canada": "Canadian",
        "france": "French",
        "germany": "German",
        "italy": "Italian",
        "spain": "Spanish",
        "brazil": "Brazilian",
        "india": "Indian",
        "japan": "Japanese",
        "south korea": "South Korean",
        "china": "Chinese",
        "mexico": "Mexican",
        "argentina": "Argentine",
        "new zealand": "New Zealander"
    }

    for country, nationality in countries.items():

        if country in place:
            return nationality

    return "Unknown"


# =========================
# MAIN
# =========================

def main():

    print("Getting the 1000 most popular actors...")

    people = get_popular_actors()

    print(f"Found {len(people)} actors.")

    actors = []

    for index, person in enumerate(people, start=1):

        print(
            f"[{index}/{len(people)}] "
            f"{person['name']}"
        )

        try:

            details, credits = get_person_data(
                person["id"]
            )

            birth_year = get_birth_year(details)

            breakout_year = get_breakout_year(
                credits
            )

            genre = get_main_genre(
                credits
            )

            nationality = get_nationality(
                details
            )

            gender = get_gender(
                details
            )

            if not birth_year:
                continue

            if not breakout_year:
                continue

            actor = {
                "id": person["id"],
                "nome": person["name"],
                "anoNascimento": birth_year,
                "anoEstourou": breakout_year,
                "popularidade": index,
                "genero": genre,
                "nacionalidade": nationality,
                "sexo": gender,
                "foto": (
                    "https://image.tmdb.org/t/p/w185"
                    + person["profile_path"]
                )
            }

            actors.append(actor)

        except Exception as error:

            print(
                f"Error with {person.get('name')}: "
                f"{error}"
            )

    with open(
        "actors.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            actors,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"Saved {len(actors)} actors."
    )


if __name__ == "__main__":
    main()
