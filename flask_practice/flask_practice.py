from flask import Flask, jsonify, render_template # render_template 추가

app = Flask(__name__)

@app.route('/') # 루트 주소로 접속하면 index.html을 보여줌
def index():
    return render_template('index.html')

@app.route('/run_python')
def run_python_script():
    data_from_python = {
        "message": "안녕하세요! Python에서 보낸 데이터입니다.",
        "items": ["항목 1", "항목 2", "항목 3"]
    }
    return jsonify(data_from_python)

if __name__ == '__main__':
    app.run(debug=True)