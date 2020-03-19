import asyncio
from flask import Flask
from flask import request
from flask import jsonify
from dbutils import get_db,close_connection,create_model,query_db
from s3utils import S3Sync

app = Flask(__name__)

@app.route('/sync', methods=['GET'])
def sync():
    path = request.args.get('path')
    bucket = request.args.get('bucket')
    sync_object = S3Sync(path, bucket)
    sync_object.sync()
    return jsonify(sync_object.to_object())

@app.route('/get', methods=['GET'])
def get():
    path = request.args.get('path')
    bucket = request.args.get('bucket')
    Sync = S3Sync(path, bucket)
    Sync.sync()
    return jsonify(Sync.to_object())

@app.before_request
def before_request():
    get_db()
    create_model()

@app.teardown_request
def teardown_request(exception):
    close_connection()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000')