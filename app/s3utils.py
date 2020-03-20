import os
import hashlib
import boto3
import time
from pathlib import Path
from bisect import bisect_left
from botocore.client import ClientError
from dbutils import save_sync,get_sync_status

# This class allows to do a synchronisation between a local path (relative to the current working directory is allowed) and an S3 bucket
# The database methods are used separately, to be able to change easily the engine if required
class S3Sync:
    def __init__(self, source=None, dest=None, storage_url=None, access_key=None, secret_key=None, wait=None):
        # We help the queries with default parameters
        self.source = source if source is not None else '.'
        self.source = os.path.join('uploads', self.source)
        self.dest = dest if dest is not None else 'mybucket'
        self.storage_url = storage_url if storage_url is not None else 'http://storage:9000'
        self.access_key = access_key if access_key is not None else os.environ['MINIO_ACCESS_KEY']
        self.secret_key = secret_key if secret_key is not None else os.environ['MINIO_SECRET_KEY']
        self._s3 = boto3.client('s3',
                                endpoint_url=self.storage_url ,
                                aws_access_key_id=self.access_key,
                                aws_secret_access_key=self.secret_key)
        # Allows to wait between each file operation, in order to test the synchronisation follow-up or cancellation
        self.wait = wait if wait is not None else 0
        self.wait = int(self.wait)
        self.status = 'running'
        self.progress = '0%'
        self.id = None
        self.id = save_sync(self)
    
    # A method to check if the synchronisation has been cancelled in the database
    def cancelled(self):
        return get_sync_status(self.id)['status'] == 'cancelled'

    # A wrapper to start the synchronisation
    def sync_files(self):
        # We check if the connection to the s3 storage is possible
        if not self.check_s3_connection():
            self.status = 'error (s3 storage connection)'
            save_sync(self)
            return
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
    
    # A method to check if the url, access key and secret key are correct
    def check_s3_connection(self):
        try:
            self._s3.list_buckets()
            return True
        except ClientError:
            return False
    
    # A method to delete the bucket if the given local path is an empty directory
    def delete_bucket(self):
        if len(self.paths) == 0:
            self._s3.delete_bucket(Bucket=self.dest)

    # A method to delete objects when they are not present in local
    def delete_objects(self):
        for key in self.objects_to_delete:
            if (self.cancelled()):
                return
            time.sleep(self.wait)
            self._s3.delete_object(Bucket=self.dest, Key=key)
            self.update_progress()

    # A method to upload the missing local files
    def upload_missing_files(self):
        for path in self.missing_files:
            if (self.cancelled()):
                return
            time.sleep(self.wait)
            self._s3.upload_file(str(Path(self.source).joinpath(path)), Bucket=self.dest, Key=path)
            self.update_progress()
    
    # A method to upload common files if they are different (md5 checksum)
    def upload_diff_files(self):
        for path in self.existing_files:
            if (self.cancelled()):
                return
            time.sleep(self.wait)
            # We use the ETag given by the s3 storage, and here we don't upload large files
            object_hash = self._s3.get_object(Bucket=self.dest, Key=path)['ETag'][1: -1]
            hasher = hashlib.md5()
            with open(str(Path(self.source).joinpath(path)), 'rb') as afile:
                buf = afile.read()
                hasher.update(buf)
            file_hash = hasher.hexdigest()
            if object_hash != file_hash:
                self._s3.upload_file(str(Path(self.source).joinpath(path)), Bucket=self.dest, Key=path)
            self.update_progress()
    
    # A method to update the synchronisation progression
    def update_progress(self):
        self.current_operations += 1
        self.progress = str(round(self.current_operations / self.total_operations * 100)) + '%'
        self.status = get_sync_status(self.id)['status']
        save_sync(self)
    
    # A method to get list of common and different files between the local source and s3 storage
    def compare_files_and_objects(self):
        self.missing_files = list(set(self.paths).difference(self.object_keys))
        self.missing_files.sort()
        self.objects_to_delete = list(set(self.object_keys).difference(self.paths))
        self.objects_to_delete.sort()
        self.existing_files = list(set(self.paths).intersection(self.object_keys))
        self.existing_files.sort()
        self.total_operations = len(self.missing_files) + len(self.objects_to_delete) + len(self.existing_files)
        self.current_operations = 0
    
    # A method to create the bucket if it doesn't exist
    def create_bucket(self):
        try:
            self._s3.head_bucket(Bucket=self.dest)
        except ClientError:
            self._s3.create_bucket(Bucket=self.dest)

    # A method to list the objects from a bucket
    def list_bucket_objects(self):
        try:
            contents = self._s3.list_objects(Bucket=self.dest)['Contents']
            self.contents = contents
        # If we don't have contents, we return an empty list
        except KeyError:
            self.contents = []
        self.object_keys = [obj['Key'] for obj in self.contents]
        self.object_keys.sort()

    # A method to list all files from a local path
    def list_source_objects(self):
        path = Path(self.source)
        paths = []
        for file_path in path.rglob("*"):
            # We don't inclure directories
            if file_path.is_dir():
                continue
            str_file_path = str(file_path)
            str_file_path = str_file_path.replace(f'{str(path)}/', "")
            paths.append(str_file_path)
        self.paths = paths
        self.paths.sort()