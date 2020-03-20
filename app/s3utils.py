import os
import hashlib
import boto3
import time
from pathlib import Path
from bisect import bisect_left
from botocore.client import ClientError
from dbutils import save_sync,get_sync_status

class S3Sync:

    def __init__(self, source=None, dest=None, storage_url=None, access_key=None, secret_key=None, wait=None):
        self.source = source if source is not None else 'uploads'
        self.dest = dest if dest is not None else 'mybucket'
        self.storage_url = storage_url if storage_url is not None else 'http://storage:9000'
        self.access_key = access_key if access_key is not None else os.environ['MINIO_ACCESS_KEY']
        self.secret_key = secret_key if secret_key is not None else os.environ['MINIO_SECRET_KEY']
        self._s3 = boto3.client('s3',
                                endpoint_url=self.storage_url ,
                                aws_access_key_id=self.access_key,
                                aws_secret_access_key=self.secret_key)
        self.wait = wait if wait is not None else 0
        self.wait = int(self.wait)
        self.status = 'init'
        self.id = None
        self.id = save_sync(self)
    
    def cancelled(self):
        return get_sync_status(self.id)['status'] == 'cancelled'

    def sync_files(self):
        self.status = 'running'
        self.id = save_sync(self)
        self.list_source_objects()
        self.create_bucket()
        self.list_bucket_objects()
        self.compare_files_and_objects()
        self.upload_missing_files()
        self.upload_diff_files()
        self.delete_objects()
        self.delete_bucket()
        if not self.cancelled():
            self.status = 'success'
            self.id = save_sync(self)
    
    def delete_bucket(self):
        if len(self.paths) == 0:
            self._s3.delete_bucket(Bucket=self.dest)

    def delete_objects(self):
        for key in self.objects_to_delete:
            if (self.cancelled()):
                return
            time.sleep(self.wait)
            self._s3.delete_object(Bucket=self.dest, Key=key)

    def upload_missing_files(self):
        for path in self.missing_files:
            if (self.cancelled()):
                return
            time.sleep(self.wait)
            self._s3.upload_file(str(Path(self.source).joinpath(path)), Bucket=self.dest, Key=path)
    
    def upload_diff_files(self):
        for path in self.existing_files:
            if (self.cancelled()):
                return
            time.sleep(self.wait)
            object_hash = self._s3.get_object(Bucket=self.dest, Key=path)['ETag'][1: -1]
            hasher = hashlib.md5()
            with open(str(Path(self.source).joinpath(path)), 'rb') as afile:
                buf = afile.read()
                hasher.update(buf)
            file_hash = hasher.hexdigest()
            if object_hash != file_hash:
                self._s3.upload_file(str(Path(self.source).joinpath(path)), Bucket=self.dest, Key=path)
    
    def compare_files_and_objects(self):
        self.missing_files = list(set(self.paths).difference(self.object_keys))
        self.missing_files.sort()
        self.objects_to_delete = list(set(self.object_keys).difference(self.paths))
        self.objects_to_delete.sort()
        self.existing_files = list(set(self.paths).intersection(self.object_keys))
        self.existing_files.sort()
    
    def create_bucket(self):
        try:
            self._s3.head_bucket(Bucket=self.dest)
        except ClientError:
            self._s3.create_bucket(Bucket=self.dest)

    def list_bucket_objects(self):
        try:
            contents = self._s3.list_objects(Bucket=self.dest)['Contents']
            self.contents = contents
        except KeyError:
            self.contents = []
        self.object_keys = [obj['Key'] for obj in self.contents]
        self.object_keys.sort()

    def list_source_objects(self):
        path = Path(self.source)
        paths = []
        for file_path in path.rglob("*"):
            if file_path.is_dir():
                continue
            str_file_path = str(file_path)
            str_file_path = str_file_path.replace(f'{str(path)}/', "")
            paths.append(str_file_path)
        self.paths = paths
        self.paths.sort()