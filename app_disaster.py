from flask import Flask, send_file
import pandas as pd

app = Flask(__name__)


# Main page
@app.route("/")
def home():

    data = pd.read_csv(
        "output/master_disaster_details.csv"
    )

    table = data.to_html(index=False)

    return f"""
    <html>
    <head>
        <title>Texas Disaster Integration</title>
    </head>

    <body>
        <h1>Texas Disaster Integration</h1>

        <p>
            Governor, SBA, and FEMA Disaster Data
        </p>

        {table}
    </body>
    </html>
    """


# Governor JSON
@app.route("/governor_disasters.json")
def governor_json():

    return send_file(
        "output/governor_disasters.json",
        mimetype="application/json"
    )


# SBA JSON
@app.route("/sba_disasters.json")
def sba_json():

    return send_file(
        "output/sba_disasters.json",
        mimetype="application/json"
    )


@app.route("/fema_disasters.json")
def fema_json():
    return send_file(
        "output/fema_disasters.json",
        mimetype="application/json"
    )

if __name__ == "__main__":
    app.run(debug=True)