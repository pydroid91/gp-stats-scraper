import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import pprint
import pandas as pd
from itertools import accumulate

HEADER = {'User-Agent': 'Mozilla/5.0'}


# seasons_url = "https://gpracingstats.com/seasons/"
# src = requests.get(seasons_url, headers=HEADER).text
# soup = BeautifulSoup(src, 'lxml')
#
# seasons_list = soup.find(class_="summary sortable season-list align-r-3 data-items-3")
# year = input()
#
# season_href = seasons_list.find("tbody").find("a", text=year).get("href")
# if season_href:
#     print(season_href)


# creates bar plots of number of best laps for drivers and constructors in certain season
def get_best_laps(year):
    bl_url = f"https://gpracingstats.com/seasons/{year}-world-championship/fastest-laps/"
    bl_src = requests.get(bl_url, headers=HEADER).text
    bl_soup = BeautifulSoup(bl_src, "lxml")

    bl_drivers = {}
    bl_constructors = {}

    for bl_row in bl_soup.find(class_="summary sortable chronology-season").find("tbody").find_all("tr"):
        driver = bl_row.find_all("td")[3].find("a").text
        constructor = bl_row.find_all("td")[4].find("a").text

        if driver not in bl_drivers:
            bl_drivers[driver] = 1
        else:
            bl_drivers[driver] += 1

        if constructor not in bl_constructors:
            bl_constructors[constructor] = 1
        else:
            bl_constructors[constructor] += 1
    plt.bar(bl_drivers.keys(), bl_drivers.values())
    plt.show()


# creates pie chart of constructors cup points in certain season
def get_constructors_cup_points(year):
    pts_url = f"https://gpracingstats.com/seasons/{year}-world-championship/constructor-standings/"
    pts_src = requests.get(pts_url, headers=HEADER).text
    pts_soup = BeautifulSoup(pts_src, "lxml")

    points = {}
    for row in pts_soup.find(class_="summary season-standings constructor").find("tbody").find_all("tr")[:-1]:
        cells = row.find_all("td")
        if not cells[1].get("style"):
            constructor, pts = cells[1].find("a").text, int(cells[-1].text)
            points[constructor] = pts

    plt.pie(points.values(), labels=points.keys())
    plt.show()


# returns point system used in certain season
def get_point_system(year):
    champ_url = f"https://gpracingstats.com/seasons/{year}-world-championship/driver-standings/"
    champ_src = requests.get(champ_url, headers=HEADER).text
    champ_soup = BeautifulSoup(champ_src, "lxml")

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
        if "float" in str(type(results[i])):
            results[i] = 0
        elif "(" in results[i]:
            results[i] = results[i][:results[i].find("(")]
        elif not results[i].isnumeric():
            results[i] = 0
        elif int(results[i]) >= len(points):
            results[i] = 0
        else:
            results[i] = points[int(results[i])]

    return results


# creates a graph of points scored during the season by drivers from the top 5 in championships
def get_championships_graph(year):
    champ_url = f"https://gpracingstats.com/seasons/{year}-world-championship/driver-standings/"

    table = pd.read_html(champ_url, index_col=0)[0]
    labels = list(table.columns)[1:-1]
    for i in range(6):
        y = list(table.iloc[i][1:-1])
        y = list(accumulate(replace_positions_with_points(y, year)))
        driver_record = table["Driver"].iloc[i]
        driver_name = driver_record[driver_record.find(")") + 1: driver_record.find("(", 2)]
        plt.plot(labels, y, label=driver_name)
    plt.legend(loc="upper left")
    plt.show()


def get_constructors_cup_graph(year):
    if year < 1958 or year > 2024:
        return
    champ_url = f"https://gpracingstats.com/seasons/{year}-world-championship/constructor-standings/"
    table = pd.read_html(champ_url, index_col=0)[0]
    labels = list(table.columns)[1:-1]
    pprint.pprint(table)
    constructors_points = {}
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
    plt.show()


# get_constructors_cup_graph(2005)
