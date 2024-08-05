
TABLES = {
    "languages": """
        CREATE TABLE languages (
            id SERIAL PRIMARY KEY, 
            name VARCHAR(255)
            )""",
    "series": """
        CREATE TABLE series (
            id SERIAL PRIMARY KEY, 
            name VARCHAR(255)
            )""",
    "users":"""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255), 
            language_id INTEGER ARRAY
            );""",
    "books": """
        CREATE TABLE books (
            id SERIAL PRIMARY KEY, 
            title TEXT NOT NULL, 
            serie_id INTEGER,
            books_numbers FLOAT(2) ARRAY,
            part_numbers FLOAT(2) ARRAY,
            author TEXT, 
            rating FLOAT(2), 
            description TEXT, 
            language_id INTEGER, 
            isbn VARCHAR(255), 
            genres VARCHAR(255) ARRAY, 
            characters VARCHAR(255) ARRAY,
            book_format VARCHAR(255),
            edition TEXT, 
            pages SMALLINT, 
            publisher TEXT, 
            publishDate VARCHAR(255), 
            firstPublishDate VARCHAR(255), 
            awards TEXT ARRAY, 
            likedPercent SMALLINT, 
            setting TEXT ARRAY, 
            coverImg TEXT,
            CONSTRAINT fk_language_id FOREIGN KEY(language_id) REFERENCES languages(id),
            CONSTRAINT fk_series_id FOREIGN KEY(serie_id) REFERENCES series(id)
            );""",
    "ratings": """
        CREATE TABLE ratings (
            id SERIAL PRIMARY KEY, 
            book_id INTEGER, 
            user_id INTEGER, 
            rating INTEGER,
            timestamp TIMESTAMP,
            CONSTRAINT fk_book_id FOREIGN KEY(book_id) REFERENCES books(id), 
            CONSTRAINT fk_user_id FOREIGN KEY(user_id) REFERENCES users(id)
            )"""
}

RECOMMANDATIONS_BY = ["standard", "author", "genres", "awards", "serie"]