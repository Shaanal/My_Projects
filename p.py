from flask import Flask, render_template, request

app = Flask(__name__)

def calculate_gpa(marks, credits):
    total_points = sum(mark * credit for mark, credit in zip(marks, credits))
    total_credits = sum(credits)
    return total_points / total_credits

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        marks = list(map(float, request.form.getlist("marks")))
        credits = list(map(float, request.form.getlist("credits")))
        gpa = calculate_gpa(marks, credits)
        return render_template("p_html.html", gpa=gpa)
    return render_template("p_html.html")

if __name__ == "__main__":
    app.run(debug=True)
