from flask import Flask, render_template, request
from scraping import *

app = Flask(__name__)


@app.route('/', methods=["GET", "POST"])
def get_inp():
    template_title = "F1 statistics"
    year = "2024"

    if request.method == "POST":
        year = request.form.get("year_inp")

    bl_img_path, bl_img2_path = get_best_laps(int(year))
    champ_graph_path = get_championships_graph(int(year))
    cc_graph_path = get_constructors_cup_graph(int(year))
    cc_pts_path = get_constructors_cup_points(int(year))

    context = {"template_title": template_title, "year": year, "bl_img": bl_img_path, "bl_img2": bl_img2_path,
               "ch_img": champ_graph_path, "cc_img": cc_graph_path, "ccpts_img": cc_pts_path}
    return render_template("index.html", context=context)


if __name__ == "__main__":
    app.run()
