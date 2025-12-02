from flask import Flask, render_template, request
from dotenv import load_dotenv
import os

#.envファイル読み込み
load_dotenv()

app = Flask(__name__)

# 質問入力画面（トップページ）
@app.route('/')
def index():
    return render_template('index.html')

# フォーム送信後の結果表示画面
@app.route('/result', methods=['POST'])
def result():
    data = request.form  # フォームから送られたデータを取得
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    return render_template(
        'result.html',
        time=data.get('time'),
        age=data.get('age'),
        gender=data.get('gender'),
        weather=data.get('weather'),
        api_key=api_key
    )

if __name__ == '__main__':
    app.run(debug=True)
