import os
import pandas as pd
import math
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from utils.comment import get_comment, load_comments
from utils.score import calculate_risk_score

load_dotenv()


#設定
app = Flask(__name__)
base_dir = os.path.dirname(os.path.abspath(__file__))

def dms_to_decimal(value, is_lat=True):
    
    value = str(value).zfill(9 if is_lat else 10)

    if is_lat:
        deg = int(value[0:2])
        minute = int(value[2:4])
        sec = int(value[4:6])
        sec_frac = int(value[6:9]) / 1000
    else:
        deg = int(value[0:3])
        minute = int(value[3:5])
        sec = int(value[5:7])
        sec_frac = int(value[7:10]) / 1000

    return deg + minute / 60 + (sec + sec_frac) / 3600

#距離計算
def calc_distance_km(lat1, lng1, lat2, lng2):
    R = 6371  # 地球半径(km)
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])

    dlat = lat2 - lat1
    dlng = lng2 - lng1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

#事故詳細表示用当事コード
def convert_vehicle(code):
    try:
        code = int(code)
    except (TypeError, ValueError):
        return "不明"

    if code == 0:
        return "不明"
    elif 1 <= code <= 5:
        return "乗用車"
    elif 11 <= code <= 14 or code == 17:
        return "貨物車"
    elif 31 <= code <= 35:
        return "二輪車"
    elif code == 36:
        return "原付"
    elif code == 41:
        return "路面電車"
    elif code == 42:
        return "列車"
    elif code == 43:
        return "電動キックボード等"
    elif code == 51 or code == 52:
        return "自転車"
    elif code == 61:
        return "歩行者"
    elif code == 75:
        return "物件等"
    elif code == 76:
        return "相手なし"
    else:
        return "その他"

# 起動時にCSV読込
def load_accident_df():
    csv_path = os.path.join(base_dir, 'data', 'accident.csv')
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding='cp932')

    # 緯度経度リネーム
    df.rename(columns={
        '地点　緯度（北緯）': 'lat',
        '地点　経度（東経）': 'lng'
    }, inplace=True)

    # 度分秒 → 十進
    df['lat'] = df['lat'].apply(lambda x: dms_to_decimal(x, is_lat=True))
    df['lng'] = df['lng'].apply(lambda x: dms_to_decimal(x, is_lat=False))
    df.dropna(subset=['lat', 'lng'], inplace=True)

    return df

# 初回起動時に実行
ACCIDENT_DF = load_accident_df()
load_comments()

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
    data = request.form
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    # 現在地
    lat = data.get("lat")
    lng = data.get("lng")
    if not lat or not lng:
        return "位置情報が取得できませんでした"

    current_lat = float(lat)
    current_lng = float(lng)

    # 入力条件
    time = data.get("time")
    age = data.get("age")
    vehicle = data.get("vehicle")
    weather = data.get("weather")

    message = get_comment(time, age, vehicle, weather)

    # =========================
    # グラフ用データ処理
    # =========================
    df_all = ACCIDENT_DF.copy()
    df_filtered = ACCIDENT_DF.copy()

    # --- 2. 年齢フィルタリング ---
    df_filtered['年齢（当事者A）'] = pd.to_numeric(
        df_filtered['年齢（当事者A）'], errors='coerce'
    )

    if age:
        target_code = None
        if "18" in age: target_code = 1
        elif "25" in age: target_code = 25
        elif "35" in age: target_code = 35
        elif "45" in age: target_code = 45
        elif "55" in age: target_code = 55
        elif "65" in age: target_code = 65
        elif "75" in age: target_code = 75

        if target_code is not None:
            df_filtered = df_filtered[df_filtered['年齢（当事者A）'] == target_code]

    # --- 3. 車種フィルタリング ---
    if vehicle:
        target_codes = []
        if "乗用車" in vehicle:
            target_codes = [1, 2, 3, 4, 5]
        elif "貨物車" in vehicle:
            target_codes = list(range(11, 18))
        elif "バイク" in vehicle:
            target_codes = list(range(31, 36))
        elif "自転車" in vehicle:
            target_codes = [51, 52]

        if target_codes:
            df_filtered = df_filtered[
                df_filtered['当事者種別（当事者A）'].isin(target_codes)
            ]

    # --- 4. 天候フィルタリング ---
    if weather:
        weather_map = {"晴": 1, "曇": 2, "雨": 3, "霧": 4, "雪": 5}
        for key, code in weather_map.items():
            if key in weather:
                df_filtered = df_filtered[df_filtered['天候'] == code]
                break

    # --- 5. 時間帯 ---
    target_hours = list(range(24))
    if time:
        if "早朝" in time: target_hours = [4, 5, 6]
        elif "午前" in time: target_hours = [7, 8, 9, 10, 11]
        elif "午後" in time: target_hours = [12, 13, 14, 15]
        elif "夕方" in time: target_hours = [16, 17]
        elif "夜" in time: target_hours = [18, 19, 20, 21]
        elif "深夜" in time: target_hours = [22, 23, 0, 1, 2, 3]

    # --- 6. 集計 ---
    hourly_counts = df_filtered['発生日時　　時'].value_counts()
    counts = [int(hourly_counts.get(h, 0)) for h in target_hours]

    # スコア
    score = calculate_risk_score(time, age, weather, vehicle)

    return render_template(
        'result.html',
        time=time,
        age=age,
        vehicle=vehicle,
        weather=weather,
        api_key=api_key,
        score=score,
        chart_labels=target_hours,
        chart_data=counts,
        message=message,
        lat=current_lat,
        lng=current_lng,
    )

#現在地周辺の20件の事故地点を表示
@app.route('/get_nearest_accidents', methods=['POST'])
def get_nearest_accidents():
    data = request.get_json()
    current_lat = float(data['lat'])
    current_lng = float(data['lng'])

    df = ACCIDENT_DF.copy()

    # 距離計算
    df['distance_km'] = df.apply(
        lambda r: calc_distance_km(current_lat, current_lng, r.lat, r.lng),
        axis=1
    )

    # 事故地点を近い順に20件
    df_near = df.sort_values('distance_km').head(20)

    # 事故詳細表示用天候コード
    WEATHER_MAP = {1: "晴", 2: "曇", 3: "雨", 4: "霧", 5: "雪"}

    result = []
    for _, row in df_near.iterrows():
        vehicle_b_code = row.get('当事者種別（当事者B）')

        result.append({
            "lat": row.lat,
            "lng": row.lng,
            "distance_km": round(row.distance_km, 2),
            "hour": int(row.get('発生日時　　時', -1)),
            "weather": WEATHER_MAP.get(row.get('天候'), "不明"),
            "vehicle_a": convert_vehicle(row.get('当事者種別（当事者A）')),
            "vehicle_b": (
                convert_vehicle(vehicle_b_code)
                if pd.notna(vehicle_b_code)
                else None
            )
        })

    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
