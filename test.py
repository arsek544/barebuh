from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return "Работает, дебил! Проверь http://127.0.0.1:5000"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)