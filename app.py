import os
import pandas as pd
import re
from flask import Flask, render_template, request
from dotenv import load_dotenv
from utils.comment import get_comment, load_comments


load_dotenv()


#設定
app = Flask(__name__)
load_comments()
base_dir = os.path.dirname(os.path.abspath(__file__))

#質問入力画面(トップページ)
@app.route('/')
def index():
    return render_template('index.html')

#ロード画面
@app.route('/loading', methods=['GET'])
def loading():
    return render_template('loading.html')

#結果画面
@app.route('/result', methods=['POST'])
def result():
    #フォームから送られてきたデータを取得
    data = request.form
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    #テスト用緯度経度をCSVと同じ形式にする（本番で削除可）
    lat = request.form.get("lat")
    lng = request.form.get("lng")
    lat_clean = lat.replace(".", "") if lat else "取得失敗"
    lng_clean = lng.replace(".", "") if lng else "取得失敗"

    #アドバイスを生成
    time = request.form["time"]
    age = request.form["age"]
    vehicle = request.form["vehicle"]
    weather = request.form["weather"]

    message = get_comment(time, age, vehicle, weather)

    #グラフ処理
        # --- 1. CSV読み込み ---
    csv_path = os.path.join(base_dir, 'data', 'accident.csv')
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding='cp932')
    except FileNotFoundError:
        return f"エラー: ファイルが見つかりません。パス: {csv_path}"

    # 数値変換（年齢用）
    df['年齢（当事者A）'] = pd.to_numeric(df['年齢（当事者A）'], errors='coerce')

    # --- 2. 年齢フィルタリング ---
    user_age_str = data.get('age')
    if user_age_str:
        target_code = None
        if "18" in user_age_str: target_code = 1
        elif "25" in user_age_str: target_code = 25
        elif "35" in user_age_str: target_code = 35
        elif "45" in user_age_str: target_code = 45
        elif "55" in user_age_str: target_code = 55
        elif "65" in user_age_str: target_code = 65
        elif "75" in user_age_str: target_code = 75
        if target_code is not None:
            df = df[df['年齢（当事者A）'] == target_code]

    # --- 3. 車種フィルタリング ---
    user_vehicle = data.get('vehicle')
    if user_vehicle:
        target_codes = []
        if "乗用車" in user_vehicle: target_codes = [3]
        elif "貨物車" in user_vehicle: target_codes = [4]
        elif "バイク" in user_vehicle: target_codes = [11, 12]
        elif "自転車" in user_vehicle: target_codes = [13, 14]
        if target_codes:
            df = df[df['当事者種別（当事者A）'].isin(target_codes)]

    # --- 4. 天候フィルタリング ---
    user_weather = data.get('weather')
    if user_weather:
        weather_code = None
        if "晴" in user_weather: weather_code = 1
        elif "曇" in user_weather: weather_code = 2
        elif "雨" in user_weather: weather_code = 3
        elif "霧" in user_weather: weather_code = 4
        elif "雪" in user_weather: weather_code = 5
        if weather_code is not None:
            df = df[df['天候'] == weather_code]
    
    # --- 5. 時間帯の絞り込み ---
    user_time_str = data.get('time')
    target_hours = list(range(24))
    if user_time_str:
        if "早朝" in user_time_str: target_hours = [4, 5, 6]
        elif "午前" in user_time_str: target_hours = [7, 8, 9, 10, 11]
        elif "午後" in user_time_str: target_hours = [12, 13, 14, 15]
        elif "夕方" in user_time_str: target_hours = [16, 17]
        elif "深夜" in user_time_str: target_hours = [22, 23, 0, 1, 2, 3]
        elif "夜" in user_time_str: target_hours = [18, 19, 20, 21]

    # --- 6. 集計とグラフデータ作成 ---
    hourly_counts = df['発生日時　　時'].value_counts()
    counts = [int(hourly_counts.get(h, 0)) for h in target_hours]

    #スコア計算
    total_accidents = sum(counts)
    score = max(0, 100 - (total_accidents * 2)) # 簡易計算
    if score < 50: score = 50 # 最低保証

    return render_template(
        'result.html',
        time=data.get('time'),
        age=data.get('age'),
        vehicle=data.get('vehicle'),
        weather=data.get('weather'),
        api_key=api_key,
        score=score,
        chart_labels=target_hours,
        chart_data=counts,
        message=message,

        #緯度経度表示(テスト用本番時削除)
        lat=lat,
        lng=lng,
        lat_clean=lat_clean,
        lng_clean=lng_clean

    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

