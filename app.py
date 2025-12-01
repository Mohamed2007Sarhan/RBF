from flask import Flask, render_template, request, jsonify
from rbf_engine import RBFEngine
import os

app = Flask(__name__)
engine = RBFEngine()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/connect', methods=['POST'])
def connect():
    data = request.json
    success = engine.connect(data['user'], data['password'], data['host'], int(data['port']))
    return jsonify({"success": success, "logs": engine.state["logs"]})

@app.route('/api/create_parent', methods=['POST'])
def create_parent():
    data = request.json
    try:
        txid = engine.create_parent(
            data['utxo_txid'], data['utxo_vout'], 
            data['amount'], data['change_addr'], data['priv_key'],
            use_v3=data.get('use_v3', False)
        )
        return jsonify({"success": True, "txid": txid, "logs": engine.state["logs"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "logs": engine.state["logs"]})

@app.route('/api/create_child', methods=['POST'])
def create_child():
    data = request.json
    try:
        txid = engine.create_child(
            data['target_addr'], data['priv_key'],
            use_v3=data.get('use_v3', False)
        )
        return jsonify({"success": True, "txid": txid, "logs": engine.state["logs"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "logs": engine.state["logs"]})

@app.route('/api/broadcast', methods=['POST'])
def broadcast():
    try:
        engine.broadcast_chain()
        return jsonify({"success": True, "logs": engine.state["logs"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "logs": engine.state["logs"]})

@app.route('/api/cancel', methods=['POST'])
def cancel():
    data = request.json
    try:
        txid = engine.cancel_parent(
            data['utxo_txid'], data['utxo_vout'], 
            data['my_addr'], data['priv_key']
        )
        return jsonify({"success": True, "txid": txid, "logs": engine.state["logs"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "logs": engine.state["logs"]})

@app.route('/api/check_status', methods=['GET'])
def check_status():
    try:
        status = engine.check_status()
        return jsonify({"success": True, "status": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(engine.state)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
