from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)

# 用于存储读取的JSON数据（这里简单示例，可优化存储结构等）
json_data_storage = {}
# 存储可用的JSON文件名列表
json_file_names = []

@app.route('/', methods=['GET', 'POST'])
def index():
    global json_data_storage, json_file_names
    if request.method == 'POST':
        try:
            file = request.files.get('json_file')
            if file:
                data = json.load(file)
                json_data_storage['current_data'] = {"file_name": file.filename, "file_content": data}
                return jsonify({"message": "Data received and stored successfully"})
            else:
                return jsonify({"message": "No file provided"}), 400
        except json.JSONDecodeError:
            return jsonify({"message": "Invalid JSON format"}), 400
    # 读取assets目录下所有json文件作为可用数据示例（可调整为按需读取不同文件等）
    json_file_names = [f for f in os.listdir('assets') if f.endswith('.json')]
    initial_data = None
    if json_file_names:
        with open(os.path.join('assets', json_file_names[0]), 'r') as f:
            initial_data = json.load(f)
            json_data_storage['current_data'] = {"file_name": json_file_names[0], "file_content": initial_data}
    return render_template('index.html', initial_data=json.dumps({"file_name": json_file_names[0], "file_content": initial_data}), file_names=json_file_names)

@app.route('/get_current_data', methods=['GET'])
def get_current_data():
    global json_data_storage
    current_data = json_data_storage.get('current_data', {})
    return jsonify({"file_name": current_data.get('file_name', ''), "file_content": current_data.get('file_content', {})})

@app.route('/get_file_names', methods=['GET'])
def get_file_names():
    global json_file_names
    json_file_names = [f for f in os.listdir('assets') if f.endswith('.json')]
    return jsonify(json_file_names)

@app.route('/load_data', methods=['POST'])
def load_data():
    global json_data_storage
    try:
        file_name = request.get_json().get('file_name')
        if file_name:
            with open(os.path.join('assets', file_name), 'r') as f:
                data = json.load(f)
                json_data_storage['current_data'] = data
                return jsonify({"message": "Data loaded successfully", "file_name": file_name, "file_content": data})
        return jsonify({"message": "No file name provided"}), 400
    except:
        return jsonify({"message": "Error loading data"}), 400

if __name__ == '__main__':
    app.run(debug=True)