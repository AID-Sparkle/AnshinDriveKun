from flask import Flask, render_template, request

app = Flask(__name__)

# 質問入力画面（トップページ）
@app.route('/')
def index():
    return render_template('index.html')

# フォーム送信後の結果表示画面
@app.route('/result', methods=['POST'])
def result():
    data = request.form  # フォームから送られたデータを取得
    return render_template(
        'result.html',
        time=data.get('time'),
        age=data.get('age'),
        gender=data.get('gender'),
        degree=data.get('degree'),
        weather=data.get('weather')
    )

if __name__ == '__main__':
    app.run(debug=True)
