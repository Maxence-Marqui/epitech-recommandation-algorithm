import pandas
import numpy as np
import time
import random
import string
import ast
import psycopg2
import psycopg2.extras
import config
import os
from scipy import spatial


def connect_to_db():
    """Open a connexion to the database using the .env informations
    """
    connexion = psycopg2.connect(
        host=os.environ["DB_HOST"],
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        port=os.environ["DB_PORT"])

    return connexion

def create_table(query: str):
    """Take a query string to create a table and execute it
    """

    conn = connect_to_db()

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        cursor.close()
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        conn.close()

def check_table_exists(table_name: str) -> bool:
    """Return a boolean depending if the tables already exists or not
    True for existing, False if not
    """

    conn = connect_to_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = '{}');".format(table_name))
        result = cursor.fetchone()[0]
        cursor.close()
    except Exception as e:
        print(e)
    finally:
        conn.close()

    return result

def create_serie(name):
    conn = connect_to_db()

    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO series VALUES (default, %s) RETURNING id;", (name,))
        serie_id = cursor.fetchall()
        conn.commit()
        cursor.close()

    except Exception as e:
        print(e)
    finally:
        conn.close()
    return serie_id[0][0]

def format_serie(serie: str):
    if not serie or serie.lower() == "nan" or type(serie) == float: return None, None, None
    splitted_serie = serie.split("#")

    if len(splitted_serie) < 2: return splitted_serie[0], None, None
    serie_name, number_identifier = splitted_serie[0], splitted_serie[1].lower()

    if "part" in number_identifier:
        if "of" in number_identifier or "/" in number_identifier:
            identifiers = number_identifier.split("part")
            identifiers[1] = identifiers[1].replace(" ","")
            if "of" in identifiers[1]:
                current, end = identifiers[1].split("of")
            if "/" in identifiers[1]:
                current, end = identifiers[1].split("/")
            return serie_name, [float("".join(filter(str.isdigit, identifiers[0].replace(" ",""))))], [float(current)]
        else:
            book_number, part_number = number_identifier.split("part")
            book_number = "".join(filter(str.isdigit, book_number))
            part_number = "".join(filter(str.isdigit, part_number))
            if not book_number or not part_number:
                return serie_name, None, None
            return serie_name, [float(book_number)], [float(part_number)]
        
    if "," in number_identifier and "-" in number_identifier and "&" in number_identifier:
        identifiers = number_identifier.split(",")
        if "-" in identifiers[0]:
            current, end = identifiers[0].split("-")
            item_array = [float(i) for i in range(int(current), int(end)+1)]
            return serie_name, item_array, None
    
    elif "," in number_identifier or ";" in number_identifier:
        if "," in number_identifier:
            identifiers = number_identifier.split(",")
        if ";" in number_identifier:
            identifiers = number_identifier.split(";")
        new_identifiers = []
        for identifier in identifiers:
            if "&" in identifier:
                i = identifier.split("&")
                try:
                    for i in identifier.split("&"): 
                        new_identifiers.append(float(i.replace(" ", "")))
                except Exception as e:
                    break
            elif "-" in identifier: 
                start, end = identifier.split("-")
                try:
                    start = float(start.replace(" ", ""))
                    end = float(end.replace(" ", ""))
                    for i in range(int(start*10),int(end*10) + 1, 10):
                        new_identifiers.append(float(i/10))
                except Exception as e:
                    break
            elif "+" in identifier:
                elements = identifier.split("+")
                for i in elements:
                    new_identifiers.append(float(i.replace(" ", "")))
            else:
                try:
                    new_identifiers.append(float("".join(filter(is_not_alpha, identifier.replace(" ", "")))))
                except Exception as e:
                    break
        return serie_name, new_identifiers, None

    if "-" in number_identifier or "–" in number_identifier:
        if "-" in number_identifier:
            identifiers = number_identifier.split("-")
        else: 
            identifiers = number_identifier.split("–")
        if len(identifiers) != 2: 
            return serie_name , [float(identifiers[0])], None
        else:
            try:
                start = float("".join(filter(str.isdigit, identifiers[0]))) * 10
                end = float("".join(filter(str.isdigit, identifiers[1]))) * 10
            except Exception as e:
                return serie_name, None, None

        books = []
        for book in range(int(start), int(end)+1):
            books.append(float(book/10))
        
        return serie_name, books, None
    
    elif "&" in number_identifier:
        elements = number_identifier.split("&")
        books = []
        for i in elements:
            try:
                books.append(float(i))
            except Exception as e:
                continue
        return serie_name, books, None
    else:
        try:
            number_identifier = float("".join(filter(str.isdigit, number_identifier.replace(" ",""))))
            return serie_name, [number_identifier], None
        except:
            return serie_name, None, None

def is_not_alpha(character:str):
    if character.isalpha(): return False
    else: return True

def str_time_prop(start, end, time_format, prop):
    """Get a time at a proportion of a range of two formatted times.

    start and end should be strings specifying times formatted in the
    given format (strftime-style), giving an interval [start, end].
    prop specifies how a proportion of the interval to be taken after
    start.  The returned time will be in the specified format.
    """

    stime = time.mktime(time.strptime(start, time_format))
    etime = time.mktime(time.strptime(end, time_format))

    ptime = stime + prop * (etime - stime)

    return time.strftime(time_format, time.localtime(ptime))

def random_date(start, end, prop):
    return str_time_prop(start, end, '%m/%d/%Y %I:%M %p', prop)

def generate_username(length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

def get_id_from_language(language, language_list):
    if type(language) == float:
        for index, language in enumerate(language_list):
            if language[0].lower() == "undetermined": return index

    for index, langue in enumerate(language_list):
        if language.lower() == langue[0].lower(): return index

def setup_db():
    for table_name, query in config.TABLES.items():
        table_exist = check_table_exists(table_name)
        if table_exist:
            print("Table {} already exists, skipping creation.".format(table_name))
        else:
            print("Creating table {}...".format(table_name))
            create_table(query)

def generate_user():
    languages_count = random.randint(1, 6)
    user_languages = set()
    for i in range(languages_count):
        user_languages.add(random.randint(1, 81))
    username = generate_username(15)
    create_user(username, list(user_languages))

def save_books(book_list: list):

    query = """
        INSERT INTO books (
            title,
            serie_id,
            books_numbers,
            part_numbers,
            author, 
            rating, 
            description, 
            language_id, 
            isbn, 
            genres, 
            characters, 
            book_format, 
            edition, 
            pages, 
            publisher, 
            publishdate, 
            firstpublishdate, 
            awards, 
            likedpercent, 
            setting, 
            coverimg
        ) VALUES %s;
    """

    conn = connect_to_db()
    conn.autocommit = True

    try:
        cursor = conn.cursor()
        psycopg2.extras.execute_values(cursor, query, book_list, page_size=500)
        cursor.close()
        conn.commit()

    except Exception as e:
        print(e)
    finally:
        conn.close()

def save_languages(languages_list):

    query = """
        INSERT INTO languages (name) VALUES %s;"""

    conn = connect_to_db()
    conn.autocommit = True

    try:
        cursor = conn.cursor()
        psycopg2.extras.execute_values(cursor, query, languages_list)
        cursor.close()
        conn.commit()

    except Exception as e:
        print(e)
    finally:
        conn.close()

def create_user(username, language):
    conn = connect_to_db()

    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users VALUES (default, %s, %s);", (username, language))
        conn.commit()
        cursor.close()

    except Exception as e:
        print(e)
    finally:
        conn.close()

def create_rating(user_id, book_id, rating, timestamp):
    conn = connect_to_db()

    query_string = """INSERT INTO ratings (book_id, user_id, rating, timestamp) VALUES (%s, %s, %s, %s);"""
    try:
        cursor = conn.cursor()
        cursor.execute(query_string, (book_id, user_id, rating, timestamp))
        conn.commit()
        cursor.close()

    except Exception as e:
        print(e)
    finally:
        conn.close()

def create_mass_ratings(ratings_list):
    conn = connect_to_db()
    query_string = """INSERT INTO ratings (user_id, book_id, rating, timestamp) VALUES %s;"""
    try:
        cursor = conn.cursor()
        psycopg2.extras.execute_values(cursor, query_string, ratings_list)
        conn.commit()
        cursor.close()

    except Exception as e:
        print(e)
    finally:
        conn.close()

def get_users_with_common_ratings(user_id):
    st = time.time()
    conn = connect_to_db()
    query_string = """
        SELECT DISTINCT u.id, COUNT(DISTINCT r1.book_id) AS common_book_count
        FROM users u
        JOIN ratings r1 ON u.id = r1.user_id
        WHERE r1.book_id IN (
            SELECT book_id
            FROM ratings
            WHERE user_id = {}
        )
        AND u.id != {}
        GROUP BY u.id
        HAVING (
                SELECT COUNT(DISTINCT book_id)
                FROM ratings r2
                WHERE r2.user_id = u.id
            ) >= 5
        ORDER BY common_book_count DESC
        LIMIT 50;
    """.format(user_id, user_id)
    try:
        cursor = conn.cursor()
        cursor.execute(query_string)
        user_list = cursor.fetchall()
        cursor.close()
    except Exception as e:
        user_list = []
    finally:
        conn.close()
    user_list = [user[0] for user in user_list]
    ed = time.time()
    print("get user with common ratings", ed - st)
    return user_list

def get_pearson_coefficient(first_user: list, second_user: list) -> float:
    first_user_average = sum(first_user) / len(first_user)
    second_user_average = sum(second_user) / len(second_user)

    for index, rating in enumerate(first_user):
        first_user[index] = rating - first_user_average
    
    for index, rating in enumerate(second_user):
        second_user[index] = rating - second_user_average

    return spatial.distance.cosine(first_user, second_user)

def get_pearson_coefficient_for_list(matrice):
    coefficient_list = []
    for index, user in enumerate(matrice):
        if index == 0: continue
        coefficient_list.append(get_pearson_coefficient(matrice[0], matrice[index]))

    return coefficient_list

def get_closests_user(target_user, user_list):
    st = time.time()
    user_list.append(target_user)
    users = get_all_ratings_from_user_list(target_user, user_list)

    user_matrice = create_users_matrix(users)
    coefficient_list = get_pearson_coefficient_for_list(user_matrice)

    coefficient_per_users = []
    for coef in coefficient_list:
        if coef < 0.6: continue
        index_coef = coefficient_list.index(coef)
        coefficient_per_users.append((user_list[index_coef], coef))
    
    coefficient_per_users.sort(key=lambda x: x[1], reverse=True)
    ed = time.time()
    print("get closest users", ed - st)
    return coefficient_per_users[0:20]

def create_users_matrix(users):

    min_id = 9999999
    max_id = 0

    for user in users:
        for rating in user:
            if rating[0] > max_id:
                max_id = rating[0]
            if rating[0] < min_id:
                min_id = rating[0]

    matrice = np.zeros((len(users), max_id - min_id))

    for index, user in enumerate(users):
        for rating in user:
            matrice[index][rating[0]- 1 - min_id] = rating[1]

    return matrice

def get_all_user_ratings(user_id):
    conn = connect_to_db()
    query_string = """SELECT book_id, rating FROM ratings WHERE user_id=%s;"""
    try:
        cursor = conn.cursor()
        cursor.execute(query_string, (user_id,))
        rating_data = cursor.fetchall()
        cursor.close()
    except Exception as e:
        print(e)
    finally:
        conn.close()

        return rating_data

def get_user_by_id(user_id):
    conn = connect_to_db()
    query_string = """SELECT * FROM users WHERE id={};""".format(user_id)
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query_string)
        user_data = cursor.fetchone()
        cursor.close()
    except Exception as e:
        print(e)
    finally:
        conn.close()

    return user_data

def get_book_by_id(book_id: int):
    conn = connect_to_db()
    query_string = """SELECT * FROM books WHERE id={};""".format(book_id)
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query_string)
        book_data = cursor.fetchone()
        cursor.close()
    except Exception as e:
        print(e)
    finally:
        conn.close()

    return book_data

def get_book_diff(first_user_id, coef_list, x_highest):
    st = time.time()

    similarities = []
    user_id_list = []
    used_id = []

    for user in coef_list:
        user_id_list.append(user[0])

    books_data = get_users_books_with_ratings(first_user_id, user_id_list)
    for book in books_data:
        for other_book in books_data:
            if book["id"] == other_book["id"]: continue
            if other_book["second_user"] == 0 : continue
            first_book, second_book, coeff = compare_books(book, other_book)
            if coeff > 20:
                similarities.append((first_book, second_book, coeff))

    if len(similarities) > 20:
        books_data = get_x_best_unread(first_user_id, 20 - len(similarities))
    
                
    similarities.sort(key=lambda x: x[2], reverse=True)
    new_similarities = []

    for comparison in similarities:
        if not comparison[1] in used_id:
            new_similarities.append(comparison)
            used_id.append(comparison[1])
    ed = time.time()
    print("book diff", ed - st, "\n")

    return new_similarities[0:x_highest]

def compare_books(first_book, second_book):

    genres = compare_genres(first_book["genres"], second_book["genres"])
    characters = compare_characters(first_book["characters"], second_book["characters"])
    author = compare_author(first_book["author"], second_book["author"])
    serie = compare_series(first_book["serie_id"], second_book["serie_id"])
    page_count = compare_page_count(first_book["pages"], second_book["pages"])
    settings = compare_settings(first_book["setting"], second_book["setting"])
    like_percentage = normalize_like_percentage(first_book["likedpercent"])

    if not genres: genres = 0
    if not characters: characters = 0
    if not author: author = 0
    if not serie: serie = 0
    if not page_count: rating = 0.5
    if not settings: settings = 0
    if not like_percentage: like_percentage = 0.5

    book_coeff = (70 * serie) + (20 * settings) + (10 * characters)
    meta_coeff = ( 60 * genres ) + ( 30 * author ) + ( 10 * page_count)

    total_coeff = (book_coeff + meta_coeff) * like_percentage * (1 + (0.05 * len(second_book["awards"]))) * (second_book["second_user"]/5)
    return (first_book["id"], second_book["id"], total_coeff)

def get_twenty_five_general_best_with_language(user_id):
    conn = connect_to_db()
    query_string = """
        SELECT b.*
        FROM books b
        JOIN users u ON u.id = {}
        WHERE b.language_id = ANY(u.language_id)
        ORDER BY b.id
        LIMIT 25
    """.format(user_id)
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query_string)
        book_data = cursor.fetchall()
        cursor.close()
    except Exception as e:
        print(e)
    finally:
        conn.close()

    return book_data

def get_x_best_unread(user_id, number):
    conn = connect_to_db()
    query_string = """
        SELECT DISTINCT b.* 
        FROM books b
        JOIN ratings r ON r.user_id = 2
        JOIN users u on u.id = r.user_id
        WHERE r.book_id != b.id
        AND b.language_id = ANY(u.language_id)
        ORDER BY b.id
        LIMIT {}
    """.format(user_id, number)
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query_string)
        book_data = cursor.fetchone()
        cursor.close()
    except Exception as e:
        print(e)
    finally:
        conn.close()

    return book_data

def get_users_books_with_ratings(first_user_id, user_id_list):
    conn = connect_to_db()

    start_time = time.time()

    query_string = """
        SELECT DISTINCT b.*, COALESCE(r1.rating, 0) AS first_user, COALESCE(r2.rating, 0) AS second_user
        FROM books b
        LEFT JOIN ratings r1 ON b.id = r1.book_id AND r1.user_id = %s
        LEFT JOIN ratings r2 ON b.id = r2.book_id AND r2.user_id = ANY(%s)
        WHERE (r1.rating IS NOT NULL OR r2.rating IS NOT NULL)
        AND b.language_id = ANY((SELECT language_id FROM users WHERE id=1)::integer[])
        AND ((b.genres && (SELECT genres FROM books WHERE id = b.id)
        OR b.author = (SELECT author FROM books WHERE id = b.id)))
    """

    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query_string, (first_user_id, user_id_list))
        book_data = cursor.fetchall()
        cursor.close()
    except Exception as e:
        print(e)
    finally:
        conn.close()

    end_time = time.time()

    print("get_users_books_with_ratings:", end_time - start_time)

    return book_data

def compare_genres(first_book_genres, second_book_genres) -> float:

    first_book_genres = set(first_book_genres)
    second_book_genres = set(second_book_genres)

    if len(first_book_genres) > len(second_book_genres):  min_genres = len(second_book_genres)
    else: min_genres = len(first_book_genres)
    
    if min_genres == 0: min_genres = 1

    intersection_len = len(first_book_genres.intersection(second_book_genres))
    return intersection_len / min_genres

def compare_characters(first_book_characters, second_book_characters) -> float:
    first_book_characters = set(first_book_characters)
    second_book_characters = set(second_book_characters)

    if len(first_book_characters) > len(second_book_characters):  min_characters = len(second_book_characters)
    else: min_characters = len(first_book_characters)
    
    if min_characters == 0: min_characters = 1

    intersection_len = len(first_book_characters.intersection(second_book_characters))
    return intersection_len / min_characters

def compare_author(first_book_author, second_book_author) -> int:
    
    if first_book_author == second_book_author: return 1
    else: return 0

def compare_series(first_book_serie:str, second_book_serie: str) -> int:
    if first_book_serie == second_book_serie: return 1
    else: return 0

def normalize_rating(rating):
    if not rating: return 0.5
    return int(rating) / 5

def compare_page_count(first_book_pages, second_book_pages):
    if not first_book_pages or not second_book_pages: return 1
    if first_book_pages < second_book_pages: return abs(int(first_book_pages) / int(second_book_pages))
    else: return abs(int(second_book_pages) / int(first_book_pages))

def compare_settings(first_book_settings, second_book_settings):
    first_book_settings = set(first_book_settings)
    second_book_settings = set(second_book_settings)

    if len(first_book_settings) > len(second_book_settings):  min_settings = len(second_book_settings)
    else: min_settings = len(first_book_settings)
    
    if min_settings == 0: min_settings = 1

    intersection_len = len(first_book_settings.intersection(second_book_settings))
    return intersection_len / min_settings

def normalize_like_percentage(liked):
    if not liked: return 0.5
    return int(liked) / 100

def compare_awards(first_book_awards, second_book_awards):

    first_book_awards = set(first_book_awards)
    second_book_awards = set(second_book_awards)

    if len(first_book_awards) > len(second_book_awards):  min_settings = len(second_book_awards)
    else: min_settings = len(first_book_awards)
    
    if min_settings == 0: min_settings = 1

    intersection_len = len(first_book_awards.intersection(second_book_awards))
    return intersection_len / min_settings

def create_indexes():
    conn = connect_to_db()

    query_string = """
        CREATE INDEX idx_user_language
        ON users USING GIN (language_id)
    """

    try:
        cursor = conn.cursor()
        cursor.execute(query_string)
        conn.commit()
        cursor.close()
    except Exception as e:
        print(e)

    query_string = """
        CREATE INDEX idx_book_language
        ON books (language_id) 
    """

    try:
        cursor = conn.cursor()
        cursor.execute(query_string)
        conn.commit()
        cursor.close()
    except Exception as e:
        print(e)

    
    query_string = """
        CREATE INDEX idx_book_genres
        ON books USING GIN (genres)
    """

    try:
        cursor = conn.cursor()
        cursor.execute(query_string)
        conn.commit()
        cursor.close()
    except Exception as e:
        print(e)

    query_string = """
        CREATE INDEX idx_ratings
        ON ratings (rating)
    """

    try:
        cursor = conn.cursor()
        cursor.execute(query_string)
        conn.commit()
        cursor.close()
    except Exception as e:
        print(e)

    query_string = """
        CREATE INDEX idx_ratings_user
        ON ratings (user_id)
    """

    try:
        cursor = conn.cursor()
        cursor.execute(query_string)
        conn.commit()
        cursor.close()
    except Exception as e:
        print(e)
    
    query_string = """
        CREATE INDEX idx_ratings_books
        ON ratings (book_id)
    """

    try:
        cursor = conn.cursor()
        cursor.execute(query_string)
        conn.commit()
        cursor.close()
    except Exception as e:
        print(e)
    
    query_string = """
        CREATE INDEX idx_user_id
        ON users (id)
    """

    try:
        cursor = conn.cursor()
        cursor.execute(query_string)
        conn.commit()
        cursor.close()
    except Exception as e:
        print(e)
    
    query_string = """
        CREATE INDEX idx_books_id
        ON books (id)
    """

    try:
        cursor = conn.cursor()
        cursor.execute(query_string)
        conn.commit()
        cursor.close()
    except Exception as e:
        print(e)

def get_count_user_ratings(user_id):
    conn = connect_to_db()
    query_string = """SELECT COUNT(*) FROM ratings WHERE user_id={};""".format(user_id)
    try:
        cursor = conn.cursor()
        cursor.execute(query_string)
        user_data = cursor.fetchone()
        cursor.close()
    except Exception as e:
        print(e)
    finally:
        conn.close()

    return user_data[0]

def get_all_ratings_from_user_list(main_user_id, user_list):
    conn = connect_to_db()
    query_string = """SELECT book_id, user_id ,rating FROM ratings WHERE user_id=ANY(%s);"""
    try:
        cursor = conn.cursor()
        cursor.execute(query_string, (user_list,))
        rating_data = cursor.fetchall()
        cursor.close()
    except Exception as e:
        print(e)
    finally:
        conn.close()

    users_ratings = {}
    for rating in rating_data:
        if rating[1] not in users_ratings: users_ratings[rating[1]] = [rating]
        else: users_ratings[rating[1]].append(rating)
    
    rating_data = [users_ratings[main_user_id]]
    for user_id in users_ratings:
        if user_id != main_user_id: rating_data.append(users_ratings[user_id])

    return rating_data

def main():
    
    setup_db()

    book_dataset = pandas.read_csv("book_dataset.csv")
    book_tuple_list = list(book_dataset.itertuples(index=False, name=None))

    """language_set = set()
    series_dict = {}

    for book in book_tuple_list:
        if book[6] and type(book[6]) != float:
            language_set.add(book[6])

    languages_list = []
    for language in language_set:
        languages_list.append((language,))
    save_languages(languages_list)


    book_list = []

    for index, book in enumerate(book_tuple_list):
        title = book[1] if book[1] else None
        serie_name, books_numbers, part_numbers = format_serie(str(book[2]))
        author = book[3] if book[3] else None
        rating = float(book[4]) if book[4] else None
        description = book[5] if book[5] else book[5]
        language = get_id_from_language(book[6], languages_list) + 1
        isbn = book[7] if book[7] else None
        genres = ast.literal_eval(book[8])
        characters = ast.literal_eval(book[9])
        book_format = book[10] if book[10] else None
        edition = book[11] if book[11] else None
        settings = ast.literal_eval(book[20])
        cover_image = book[21] if book[21] else None
        publisher = book[13] if book[13] else None
        publish_date = book[14] if book[14] else None
        first_publication = book[15] if book[15] else None
        awards = ast.literal_eval(book[16])

        try:
            pages = int(book[12])
        except:
            pages = None

        try:
            liked_percentage = int(book[19])
        except:
            liked_percentage = None

        if serie_name:
            if serie_name not in series_dict:
                serie_id = create_serie(serie_name)
                series_dict[serie_name] = serie_id
            else:
                serie_id = series_dict[serie_name]
        else: serie_id = None
        
        book_list.append(
            (
                title,
                serie_id,
                books_numbers,
                part_numbers,
                author,
                rating,
                description,
                language,
                isbn,
                genres,
                characters,
                book_format,
                edition,
                pages,
                publisher,
                publish_date,
                first_publication,
                awards,
                liked_percentage,
                settings,
                cover_image
            )
        )

    save_books(book_list)

    for i in range(1, 10001):
        generate_user()
        user_ratings = []
        number_of_ratings = random.randrange(10, 50)
        for j in range(number_of_ratings):
            user_ratings.append((i, random.randrange(1, 52479), random.randrange(1, 6), random_date('1/1/1950 12:00 PM', '1/1/2023 12:00 PM', random.random())))
        create_mass_ratings(user_ratings)


    create_indexes()"""

    user_to_test = [1, 20, 300, 4000, 5, 11, 222, 3333,10001]

    time_list = []

    for id in user_to_test:
        start_time = time.time()
        book_comparisons = []

        user_list = get_users_with_common_ratings(id)
        rating_count = get_count_user_ratings(id)

        if user_list and rating_count:
            users_coeff = get_closests_user(id, user_list)
            book_similarities = get_book_diff(id, users_coeff, 25)
            for book in book_similarities:
                book_comparisons.append((get_book_by_id(book[0]), get_book_by_id(book[1]), book[2]))
            for comparisons in book_comparisons:
                print("Le livre {} (id: {}) est proche de {} (id: {}), le score de similarité est de {}".format(comparisons[0]["title"], comparisons[0]["id"], comparisons[1]["title"],comparisons[1]["id"] , comparisons[2]))

        else:
            book_comparisons = get_twenty_five_general_best_with_language(id)
            for book in book_comparisons:
                print("Pour un débutant je recommande: {} (id: {}).".format(book["title"], book["id"]))
            

        end_time = time.time()
        time_list.append(end_time - start_time)
        print("\nTemps d'execution: {} secondes.".format(end_time - start_time))
        print("------------------------------------------")

    print("Temps moyen = {} secondes".format(sum(time_list) / len(user_to_test)))

if __name__ == '__main__':
    main()