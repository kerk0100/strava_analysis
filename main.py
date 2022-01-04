from flask import Flask, request, render_template, jsonify, redirect, make_response
from load_data import load, distance
import csv
import sys
import pickle

csv.field_size_limit(sys.maxsize)

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")
    
@app.route("/filtering", methods =["GET", "POST"])
def filtering():
    if request.method == "POST":
       # getting input with name = selectType, etc.. in HTML form
       metrics = request.form.getlist('metric')
       metrics.insert(0, "id")
       try:
           a_type = request.form.get("selectType")
       except:
           a_type = "--"
       try:
           operand = request.form.get("selectOp")
       except:
           operand = "--"
       try:
           dist = int(request.form.get("dist"))
       except:
           dist = 0
  
       with open('static/data/data.txt', 'rb') as f:
            activities = pickle.load(f)
       activity_data = activities
       results = distance(int(dist), str(a_type), str(operand), activity_data, metrics)
       activities_filtered = []
       for a in results:
           activities_filtered.append(a)
       return render_template("filtering.html", column_names=results.columns.values, row_data=list(results.values.tolist()), zip=zip)
    return render_template("filtering.html")

@app.route("/join")
def join():
    return render_template("join.html")

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



