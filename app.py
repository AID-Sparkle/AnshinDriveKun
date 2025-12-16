from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
import pandas as pd
import re

# .envファイル（環境変数）を読み込みます。
# APIキーなどの重要な情報をコードに直書きせず、別ファイルで管理するために使います。
load_dotenv()

# --- アプリケーションの初期設定 ---

# 現在のファイル(app.py)がある場所（ディレクトリ）のパスを取得します。
base_dir = os.path.dirname(os.path.abspath(__file__))

# staticフォルダ（CSSや画像ファイル置き場）の場所をここで指定します。
# 今回の構成では .vscode/data/static にあるため、そのパスを組み立てています。
static_folder_path = os.path.join(base_dir, '.vscode', 'data', 'static')

# Flaskアプリの本体を作成します。staticフォルダの場所もここで教えてあげます。
app = Flask(__name__, static_folder=static_folder_path)


# --- ルーティング設定（URLごとの処理） ---

# トップページ（http://localhost:5000/）にアクセスしたときの処理
@app.route('/')
def index():
    # templatesフォルダ内の index.html（質問入力画面）を表示します
    return render_template('index.html')


# 診断ボタンを押してデータが送信されたときの処理（/result）
@app.route('/result', methods=['POST'])
def result():
    # フォームから送信されたデータ（ユーザーの回答内容）を受け取ります
    data = request.form
    
    # 環境変数からGoogle Mapsを使うための鍵（APIキー）を取得します
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    # --- 1. CSVファイルの読み込み ---
    
    # 読み込むCSVファイルのパスを作成します（.vscode/data/accident.csv）
    csv_path = os.path.join(base_dir, '.vscode', 'data', 'accident.csv')
    
    try:
        # まず一般的なUTF-8形式で読み込みを試みます
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        # 失敗したら日本語Windowsでよく使われるShift-JIS (cp932) で読み込みます
        df = pd.read_csv(csv_path, encoding='cp932')
    except FileNotFoundError:
        # ファイル自体が見つからない場合はエラーメッセージを返して終了します
        return f"エラー: ファイルが見つかりません。パス: {csv_path}"

    # データの「年齢」カラムを計算できるように数値に変換しておきます
    # 文字が入っているなど変換できないデータは 'coerce' で強制的に無効値(NaN)にします
    df['年齢（当事者A）'] = pd.to_numeric(df['年齢（当事者A）'], errors='coerce')


    # --- 2. 年齢によるデータの絞り込み ---
    
    user_age_str = data.get('age') # フォームから「年齢」の回答を取得
    
    if user_age_str:
        target_code = None
        # 選択された年齢層に合わせて、データ上の「年齢コード」を決めます
        # (例: データ上では '1' が若年層、'25' が25-34歳... となっているため)
        if "18" in user_age_str: target_code = 1
        elif "25" in user_age_str: target_code = 25
        elif "35" in user_age_str: target_code = 35
        elif "45" in user_age_str: target_code = 45
        elif "55" in user_age_str: target_code = 55
        elif "65" in user_age_str: target_code = 65
        elif "75" in user_age_str: target_code = 75
        
        # 該当するコードを持つデータだけを残します（フィルタリング）
        if target_code is not None:
            df = df[df['年齢（当事者A）'] == target_code]


    # --- 3. 車種によるデータの絞り込み ---
    
    user_vehicle = data.get('vehicle') # フォームから「車種」の回答を取得
    
    if user_vehicle:
        target_codes = []
        # データ上の「当事者種別コード」に合わせてリストを作ります
        # (例: 3=乗用車, 4=貨物車, 11=バイク, 13=自転車...)
        if "乗用車" in user_vehicle: target_codes = [3]
        elif "貨物車" in user_vehicle: target_codes = [4]
        elif "バイク" in user_vehicle: target_codes = [11, 12] # 自動二輪と原付
        elif "自転車" in user_vehicle: target_codes = [13, 14]
        
        # リストに含まれるコードのいずれかに一致するデータだけを残します
        if target_codes:
            df = df[df['当事者種別（当事者A）'].isin(target_codes)]


    # --- 4. 天候によるデータの絞り込み ---
    
    user_weather = data.get('weather') # フォームから「天候」の回答を取得
    
    if user_weather:
        weather_code = None
        # データ上の「天候コード」に変換します (1=晴れ, 2=曇り, 3=雨...)
        if "晴" in user_weather: weather_code = 1
        elif "曇" in user_weather: weather_code = 2
        elif "雨" in user_weather: weather_code = 3
        elif "霧" in user_weather: weather_code = 4
        elif "雪" in user_weather: weather_code = 5
        
        # 該当する天候コードのデータだけを残します
        if weather_code is not None:
            df = df[df['天候'] == weather_code]
    

    # --- 5. 時間帯による表示範囲の設定 ---
    
    user_time_str = data.get('time') # フォームから「時間帯」の回答を取得
    
    # デフォルト（未選択時）は0時〜23時の全時間を対象にします
    target_hours = list(range(24))
    
    # 選択された時間帯に応じて、グラフに表示する時間のリストを作ります
    if user_time_str:
        if "早朝" in user_time_str: target_hours = [4, 5, 6]
        elif "午前" in user_time_str: target_hours = [7, 8, 9, 10, 11]
        elif "午後" in user_time_str: target_hours = [12, 13, 14, 15]
        elif "夕方" in user_time_str: target_hours = [16, 17]
        # 深夜は日付をまたぐため、22時〜翌3時までを指定します
        elif "深夜" in user_time_str: target_hours = [22, 23, 0, 1, 2, 3]
        elif "夜" in user_time_str: target_hours = [18, 19, 20, 21]


    # --- 6. 集計とグラフ用データの作成 ---
    
    # ここまでで絞り込まれたデータの、「発生日時　　時」ごとの件数を数えます
    hourly_counts = df['発生日時　　時'].value_counts()
    
    # 表示対象の時間（target_hours）の件数だけをリスト形式にします
    # データがない時間帯は .get(h, 0) で「0件」として扱います
    counts = [int(hourly_counts.get(h, 0)) for h in target_hours]
    

    # --- 7. 結果画面へのデータ渡し ---
    
    # render_templateを使って result.html を表示しつつ、必要なデータを渡します
    return render_template(
        'result.html',
        # 画面表示用：ユーザーが入力した内容をそのまま渡します
        time=data.get('time'),
        age=data.get('age'),
        vehicle=data.get('vehicle'),
        weather=data.get('weather'),
        
        # システム用：Google Maps APIキー
        api_key=api_key,
        
        # グラフ用：X軸（時間）とY軸（件数）のリスト
        chart_labels=target_hours,
        chart_data=counts
    )

# このファイルが直接実行されたときにサーバーを起動します
if __name__ == '__main__':
    app.run(debug=True)