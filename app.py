from flask import Flask, render_template, request, send_file
from scraping import parse_all_plots
import sqlite3
import io

app = Flask(__name__)
db = "images.db"


def create_db():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                year INTEGER PRIMARY KEY,
                bl_image BLOB,
                bl_image2 BLOB,
                champ_graph_image BLOB,
                cc_graph_image BLOB,
                cc_pts_image BLOB
            )
        ''')


def check_images(year):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT year FROM images WHERE year = ?", (year,))
    return cursor.fetchone()


def upload_image_to_db(year, images):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO images VALUES (?, ?, ?, ?, ?, ?)',
                   (int(year), images[0].read(), images[1].read(), images[2].read(), images[3].read(), images[4].read()))
    conn.commit()
    conn.close()


def get_images(year):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    cursor.execute('''SELECT * FROM images WHERE year = ?''', (year,))
    return cursor.fetchone()


@app.route('/', methods=["GET", "POST"])
def get_inp():
    context = {"template_title": "F1 statistics"}
    year = "2024"

    if request.method == "POST":
        year = request.form.get("year_inp")
        if not year.isnumeric():
            year = "2024"
        elif int(year) < 1950 or int(year) > 2024:
            year = None

    if year:
        create_db()
        if not check_images(year):
            plots = parse_all_plots(int(year))
            upload_image_to_db(year, plots)

        for i in range(1, 6):
            get_plot(year, i)
        context["year"] = year
    else:
        for i in range(1, 6):
            get_plot("2024", i)
        context["year"] = 0

    return render_template("index.html", context=context)


@app.route('/plot/<int:year>/<int:number>')
def get_plot(year, number):
    if year == 0:
        year = "2024"
    image_data = get_images(year)[number]

    if image_data:
        return send_file(io.BytesIO(image_data), mimetype='image/png')
    else:
        return "График не найден"


if __name__ == "__main__":
    app.run()
