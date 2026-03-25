from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/hello', methods=['GET'])
def hello():
    
    return jsonify({"message": "Hello from Flask API!"})

@app.route('/api/goodbye', methods=['GET'])
def goodbye():
    return jsonify({"message": "Goodbye from Flask API!"})

@app.route('/')
def home():
    return "<h1>Welcome to Noey's Flask API</h1><p>Try /api/hello or /api/goodbye</p>"