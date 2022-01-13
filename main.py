from flask import Flask, request, render_template, jsonify, redirect, make_response
from load_data import graph_data, load, distance
import csv
import sys
import pickle
import time
import json
import plotly
from flask import Markup
# use for displaying graphs in webpage
# from dash import Dash
# import dash_core_components as dcc
# import dash_html_components as html

csv.field_size_limit(sys.maxsize)

app = Flask(__name__)

# TODO: "/" route should be login, and not index
@app.route("/")
def index():
    return render_template("index.html")

# execute when user on filtering page
@app.route("/filtering", methods =["GET", "POST"])
def filtering():
    if request.method == "POST":
       # getting input with name = selectType, etc.. in HTML form
       metrics = request.form.getlist('metric')
       # include id in all the queries (id includes link to activity)
       metrics.insert(0, "id")
       try:
           a_type = request.form.get("selectType")
       except:
           a_type = "--"
    
       operand = request.form.get("selectOp")
       if operand == "greater":
           operand = ">"
       elif operand == "less":
           operand = "<"
       elif operand == "equal":
           operand = "="
       else:
           operand = "--"

       try:
           try:
                dist = int(request.form.get("other_dist")) * 1000
           except:
               dist = int(request.form.get("swim_dist"))
       except:
           dist = 0   
       try:
           start_date = request.form.get("trip-start")
           start_date = time.strptime(start_date, "%Y-%m-%d")
       except:
           start_date = 0
       try:
           end_date = request.form.get("trip-end")
           end_date = time.strptime(end_date, "%Y-%m-%d")
       except:
           end_date = 0
       with open('static/data/data.txt', 'rb') as f:
            activities = pickle.load(f)
       activity_data = activities
       results = distance(int(dist), str(a_type), str(operand), activity_data, metrics, start_date, end_date)
       activities_filtered = []
       for a in results:
           activities_filtered.append(a)
       return render_template("filtering.html", column_names=results.columns.values, row_data=list(results.values.tolist()), zip=zip)
    return render_template("filtering.html")

@app.route("/join")
def join():
    return render_template("join.html")

@app.route("/graphs", methods=['GET', 'POST'])
def graph():
    if request.method == "POST":
        years = []
        temp = request.form.getlist('year')
        for y in temp:
            years.insert(0,y)
        graph = graph_data(years)
        # graphJSON = json.dumps(graph, cls=plotly.utils.PlotlyJSONEncoder)
        return render_template('graphs.html', plot= Markup(graph))
        # return render_template("graphs.html", graphJSON=graphJSON)
    return render_template("graphs.html")

@app.route("/login", methods =["GET", "POST"])
def login():
    if request.method == "POST":
        id = request.form.get("client_id")
        secret = request.form.get("client_secret")
        refresh = request.form.get("refresh_token")
        load(id,secret,refresh)
        return redirect("/")
    return render_template("login.html")
    
if __name__ == "__main__":
    app.run(debug=True)



