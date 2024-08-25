import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, request, send_file, jsonify
from flask_socketio import SocketIO, emit
import requests
import csv
import math
import os
import logging
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*", logger=True, engineio_logger=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

BASE_URL = "https://api-sscasn.bkn.go.id/2024/portal/spf"
headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
    "Connection": "keep-alive",
    "Host": "api-sscasn.bkn.go.id",
    "Origin": "https://sscasn.bkn.go.id",
    "Referer": "https://sscasn.bkn.go.id/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
    "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Microsoft Edge\";v=\"127\", \"Chromium\";v=\"127\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}

gabungan_data = []
tingkat_pendidikan_data = []

def load_gabungan_data():
    global gabungan_data
    with open('gabungan.csv', mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        gabungan_data = [row for row in reader]

def load_tingkat_pendidikan_data():
    global tingkat_pendidikan_data
    with open('tingkat_pendidikan_data.csv', mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        tingkat_pendidikan_data = [row for row in reader]

load_gabungan_data()
load_tingkat_pendidikan_data()

@app.route('/')
def index():
    return render_template('combined.html')

@app.route('/api/tingkat_pendidikan')
def api_tingkat_pendidikan():
    tingkat_pendidikan_options = [
        {"id": row["id"], "nama": row["nama"]}
        for row in tingkat_pendidikan_data
    ]
    return jsonify(tingkat_pendidikan_options)

@app.route('/api/program_studi')
def api_program_studi():
    tingkat_pendidikan_id = request.args.get('tingkat_pendidikan_id')
    if not tingkat_pendidikan_id:
        return jsonify({"error": "Missing tingkat_pendidikan_id parameter"}), 400

    program_studi_set = {row['nama_program_studi'] for row in gabungan_data if row['tingkat_pendidikan_id'] == tingkat_pendidikan_id}
    program_studi = sorted(list(program_studi_set))
    return jsonify(program_studi)

@app.route('/api/get_cepat_kode')
def api_get_cepat_kode():
    tingkat_pendidikan_id = request.args.get('tingkat_pendidikan_id')
    program_studi = request.args.get('program_studi')

    if not tingkat_pendidikan_id or not program_studi:
        return jsonify({"error": "Missing parameters"}), 400

    for row in gabungan_data:
        if row['tingkat_pendidikan_id'] == tingkat_pendidikan_id and row['nama_program_studi'] == program_studi:
            return jsonify({"cepat_kode": row['cepat_kode']})

    return jsonify({"error": "No matching cepat_kode found"}), 404

@app.route('/fetch-records', methods=['GET'])
def fetch_records():
    kode_ref_pend = request.args.get('kode_ref_pend')
    if not kode_ref_pend:
        emit_log("Error: Missing kode_ref_pend parameter")
        return jsonify({"error": "kode_ref_pend parameter is required"}), 400

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    csv_file_name = f"{kode_ref_pend}_records_{timestamp}.csv"
    emit_log(f"kode_ref_pend: {kode_ref_pend}")

    try:
        response = requests.get(f"{BASE_URL}?kode_ref_pend={kode_ref_pend}&offset=0", headers=headers)
        response.raise_for_status()
        data = response.json()

        total_records = data['data']['meta']['total']
        records_per_page = len(data['data']['data'])
        total_pages = math.ceil(total_records / records_per_page)

        emit_log(f"Total records: {total_records}, Total pages: {total_pages}")

        with open(csv_file_name, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            for page in range(total_pages):
                offset = page * records_per_page
                emit_log(f"Fetching page {page + 1}/{total_pages} (offset: {offset})")
                eventlet.sleep(0)  # Yield control to ensure logs are sent in real-time

                response = requests.get(f"{BASE_URL}?kode_ref_pend={kode_ref_pend}&offset={offset}", headers=headers)
                response.raise_for_status()
                data = response.json()

                if page == 0:
                    writer.writerow(data['data']['data'][0].keys())
                    emit_log("CSV header written")
                    eventlet.sleep(0)

                for record in data['data']['data']:
                    writer.writerow(record.values())

        emit_log(f"Saved to {csv_file_name}")

        return send_file(csv_file_name, as_attachment=True)

    except requests.HTTPError as http_err:
        emit_log(f"HTTP error occurred: {http_err}")
        return jsonify({"error": f"HTTP error occurred: {http_err}"}), 500
    except Exception as err:
        emit_log(f"An error occurred: {err}")
        return jsonify({"error": f"An error occurred: {err}"}), 500

def emit_log(message):
    """Emit a log message to the frontend via WebSocket."""
    socketio.emit('log', {'message': message})
    logging.info(message)
    socketio.sleep(0)  # Yield control to ensure logs are sent in real-time

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
