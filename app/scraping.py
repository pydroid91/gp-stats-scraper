import matplotlib
matplotlib.use("Agg")
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import pandas as pd
from itertools import accumulate
import io

HEADER = {'User-Agent': 'Mozilla/5.0'}


def save_plot():
    b = io.BytesIO()
    plt.savefig(b, format="png")
    b.seek(0)
    plt.close()
    return b


def save_empty_cc_plot():
    plt.figure()
    plt.plot()
    plt.text(0, 0, "Кубок конструкторов впервые начал разыгрываться в 1958г.", ha="center", va="center")
    plt.axis("off")
    b = io.BytesIO()
    plt.savefig(b, format="png")
    b.seek(0)
    plt.close()
    return b


def save_best_laps_plots(info_dict, title):
    plt.figure()
    plt.bar(info_dict.keys(), info_dict.values())
    plt.title(f"Количество лучших кругов (по {title})")
    plt.xticks(fontsize=8)
    b = save_plot()
    return b


def get_soup(url):
    src = requests.get(url, headers=HEADER).text
    return BeautifulSoup(src, "lxml")


# creates bar plots of number of best laps for drivers and constructors in certain season
def get_best_laps(year):
    bl_soup = get_soup(f"https://gpracingstats.com/seasons/{year}-world-championship/fastest-laps/")

    bl_drivers = {}
    bl_constructors = {}

    for bl_row in bl_soup.find(class_="summary sortable chronology-season").find("tbody").find_all("tr"):
        try:
            driver = bl_row.find_all("td")[3].find("a").text
            driver = driver.split()[1][:3].upper()
            constructor = bl_row.find_all("td")[4].find("a").text
        except AttributeError:
            continue

        if driver not in bl_drivers:
            bl_drivers[driver] = 1
        else:
            bl_drivers[driver] += 1

        if constructor not in bl_constructors:
            bl_constructors[constructor] = 1
        else:
            bl_constructors[constructor] += 1

    return [save_best_laps_plots(bl_constructors, "командам"), save_best_laps_plots(bl_drivers, "пилотам")]


# creates pie chart of constructors cup points in certain season
def get_constructors_cup_points(year):
    if year < 1958:
        return save_empty_cc_plot()

    pts_soup = get_soup(f"https://gpracingstats.com/seasons/{year}-world-championship/constructor-standings/")

    points = {}
    for row in pts_soup.find(class_="summary season-standings constructor").find("tbody").find_all("tr")[:-1]:
        cells = row.find_all("td")
        if not cells[1].get("style"):
            pts = cells[-1].text
            if "(" in pts:
                pts = pts[:pts.find("(") - 1]
            if "." in pts:
                pts = pts[:pts.find("(") - 1]
            if not str(pts).isnumeric():
                break

            if "(" in pts:
                pts = pts[:pts.find("(")]
            pts = int(pts)
            constructor = cells[1].find("a").text
            points[constructor] = pts

    plt.figure()
    plt.pie(points.values(), labels=points.keys(), autopct='%1.0f%%', radius=1.3)
    plt.title("Распределение очков кубка конструкторов")
    return save_plot()


# returns point system used in certain season
def get_point_system(year):
    champ_soup = get_soup(f"https://gpracingstats.com/seasons/{year}-world-championship/driver-standings/")

    points = [0]
    fastest_lap_point = 0
    for li in champ_soup.find_all(class_="key")[0].find_all("ul")[-1].find_all("li"):
        line = li.text
        if "fastest" in line:
            fastest_lap_point = int(line[line.find("(") + 1:line.find(")")])
        else:
            points.append(int(line[line.find("(") + 1:line.find(")")]))
    return points, fastest_lap_point


def replace_positions_with_points(results, year):
    points, fl_points = get_point_system(year)

    for i in range(len(results)):
        if "float" in str(type(results[i])) or not results[i].isnumeric():
            results[i] = 0
            continue
        if "(" in results[i]:
            results[i] = results[i][:results[i].find("(")]
        if int(results[i]) >= len(points):
            results[i] = 0
        else:
            results[i] = points[int(results[i])]
    return results


# creates a graph of points scored during the season by drivers from the top 5 in championships
def get_championships_graph(year):
    champ_url = f"https://gpracingstats.com/seasons/{year}-world-championship/driver-standings/"

    table = pd.read_html(champ_url, index_col=0)[0]
    labels = list(table.columns)[1:-1]
    plt.figure()
    for i in range(6):
        y = list(table.iloc[i][1:-1])
        y = list(accumulate(replace_positions_with_points(y, year)))
        driver_record = table["Driver"].iloc[i]
        driver_name = driver_record[driver_record.find(")") + 1: driver_record.find("(", 2)]
        plt.plot(labels, y, label=driver_name)

    plt.legend(loc="upper left")
    plt.xticks(rotation=90)
    plt.title("График очков чемпионата")
    return save_plot()


def get_constructors_cup_graph(year):
    if year < 1958:
        return save_empty_cc_plot()

    champ_url = f"https://gpracingstats.com/seasons/{year}-world-championship/constructor-standings/"
    table = pd.read_html(champ_url, index_col=0)[0]
    labels = list(table.columns)[1:-1]

    constructors_points = {}
    plt.figure()
    for i in range(len(table.index) - 1):
        constructor_record = table["Constructor"].iloc[i]
        constructor = constructor_record[constructor_record.find(")") + 1:]
        if constructor not in constructors_points and len(constructors_points) == 10:
            break

        y = list(table.iloc[i][1:-1])
        y = pd.Series(accumulate(replace_positions_with_points(y, year)))
        if constructor not in constructors_points:
            constructors_points[constructor] = y
        else:
            constructors_points[constructor] += y

    for constructor in constructors_points:
        plt.plot(labels, constructors_points[constructor], label=constructor)

    plt.legend(loc="upper left")
    plt.xticks(rotation=90)
    plt.title("График очков кубка конструкторов")

    return save_plot()


def parse_all_plots(year):
    plots = []
    plots.extend(get_best_laps(year))
    plots.append(get_championships_graph(year))
    plots.append(get_constructors_cup_graph(year))
    plots.append(get_constructors_cup_points(year))
    return plots
