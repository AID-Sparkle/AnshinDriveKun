from flask import Flask, render_template, request
from dotenv import load_dotenv
from utils.comment import get_comment, load_comments
import os

load_dotenv()

app = Flask(__name__)
load_comments()

# 🔹質問入力画面(トップページ)
@app.route('/')
def index():
    return render_template('index.html')

# 🔹ロード画面
@app.route('/loading', methods=['GET'])
def loading():
    return render_template('loading.html')

# 🔹結果画面
@app.route('/result', methods=['POST'])
def result():
    data = request.form
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    lat = request.form.get("lat")
    lng = request.form.get("lng")

    lat_clean = lat.replace(".", "") if lat else "取得失敗"
    lng_clean = lng.replace(".", "") if lng else "取得失敗"

    time = request.form["time"]
    age = request.form["age"]
    gender = request.form["gender"]
    weather = request.form["weather"]

    message = get_comment(time, age, gender, weather)

    return render_template(
        'result.html',
        time=data.get('time'),
        age=data.get('age'),
        gender=data.get('gender'),
        weather=data.get('weather'),
        api_key=api_key,
        lat=lat,
        lng=lng,
        lat_clean=lat_clean,
        lng_clean=lng_clean,
        message=message
    )

if __name__ == '__main__':
    app.run(debug=True)
