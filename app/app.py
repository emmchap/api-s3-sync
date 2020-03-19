from flask import Flask
from flask import request
from flask import jsonify
from dbutils import dbModel
from s3utils import S3Sync

app = Flask(__name__)

@app.route('/sync', methods=['GET'])
def sync():
    path = request.args.get('path')
    bucket = request.args.get('bucket')
    Sync = S3Sync(path, bucket)
    Sync.sync()
    return jsonify(Sync.to_object())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000')