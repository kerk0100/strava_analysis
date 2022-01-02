from flask import Flask, request, render_template, jsonify
from load_data import load, distance

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
       activity_data = load()
       results = distance(int(dist), str(a_type), str(operand), activity_data)
       activities_filtered = []
       for a in results:
           activities_filtered.append(a)
       return jsonify(activities_filtered)
    return render_template("filtering.html")

@app.route("/join")
def join():
    return render_template("join.html")
    
if __name__ == "__main__":
    app.run(debug=True)

