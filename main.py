from flask import Flask, request, render_template, jsonify, redirect
from load_data import load, distance
import csv
import sys

csv.field_size_limit(sys.maxsize)

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")
    
@app.route("/filtering", methods =["GET", "POST"])
def filtering():
    if request.method == "POST":
       # getting input with name = selectType, etc.. in HTML form
       a_type = request.form.get("selectType")
       operand = request.form.get("selectOp")
       dist = int(request.form.get("dist"))
       with open('static/data.csv', newline='') as f:
            reader = csv.reader(f)
            data = list(reader)
       activity_data = data
       results = distance(int(dist), str(a_type), str(operand), activity_data)
       activities_filtered = []
       for a in results:
           activities_filtered.append(a)
       return jsonify(activities_filtered)
    return render_template("filtering.html")

@app.route("/join")
def join():
    return render_template("join.html")

@app.route("/login", methods =["GET", "POST"])
def login():
    if request.method == "POST":
        activities = load()
        with open('static/data.csv', 'w', newline='') as csvfile:
            wr = csv.writer(csvfile)
            wr.writerow(activities)
        return redirect("/")
    return render_template("login.html")
    
if __name__ == "__main__":
    app.run(debug=True)



