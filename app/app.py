import asyncio
from flask import Flask
from flask import request
from flask import jsonify
from dbutils import get_db,close_connection,create_model,get_sync_status,get_running_syncs,cancel_sync
from s3utils import S3Sync

app = Flask(__name__)

@app.route('/sync', methods=['GET'])
def sync():
    source = request.args.get('source')
    dest = request.args.get('dest')
    storage_url = request.args.get('storage_url')
    access_key = request.args.get('access_key')
    secret_key = request.args.get('secret_key')
    wait = request.args.get('wait')
    sync_object = S3Sync(source=source, dest=dest, storage_url=storage_url, access_key=access_key, secret_key=secret_key, wait=wait)
    sync_object.sync_files()
    return jsonify(get_sync_status(sync_object.id))

@app.route('/get', methods=['GET'])
def get():
    id = request.args.get('id')
    return jsonify(get_sync_status(id))

@app.route('/runnings', methods=['GET'])
def runnings():
    return jsonify(get_running_syncs())

@app.route('/cancel', methods=['GET'])
def stop():
    id = request.args.get('id')
    cancel_sync(id)
    return jsonify(get_sync_status(id))

@app.before_request
def before_request():
    get_db()
    create_model()

@app.teardown_request
def teardown_request(exception):
    close_connection()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000')