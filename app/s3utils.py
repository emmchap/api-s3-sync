import os
import hashlib
from pathlib import Path
from bisect import bisect_left
import boto3

class S3Sync:

    def __init__(self, local_path, bucket, storage_url=None, access_key=None, secret_key=None):
        self.source = local_path
        self.dest = bucket
        self.storage_url = storage_url if storage_url is not None else 'http://storage:9000'
        access_key = access_key if access_key is not None else os.environ['MINIO_ACCESS_KEY']
        secret_key = secret_key if secret_key is not None else os.environ['MINIO_SECRET_KEY']
        self._s3 = boto3.client('s3',
                                endpoint_url=self.storage_url ,
                                aws_access_key_id=access_key,
                                aws_secret_access_key=secret_key)

    def sync(self):
        self.list_source_objects()
        self.list_bucket_objects()

        # Getting the keys and ordering to perform binary search
        # each time we want to check if any paths is already there.
        object_keys = [obj['Key'] for obj in self.contents]
        object_keys.sort()
        file_paths = self.paths
        file_paths.sort()

        missing_files = list(set(file_paths).difference(object_keys))
        objects_to_delete = list(set(object_keys).difference(file_paths))
        existing_files= list(set(file_paths).intersection(object_keys))

        for path in missing_files:
            self._s3.upload_file(str(Path(self.source).joinpath(path)), Bucket=self.dest, Key=path)

        for path in existing_files:
            s3object = self._s3.get_object(Bucket=self.dest, Key=path)
            object_hash = s3object['ETag'][1: -1]
            hasher = hashlib.md5()
            with open(str(Path(self.source).joinpath(path)), 'rb') as afile:
                buf = afile.read()
                hasher.update(buf)
            file_hash = hasher.hexdigest()
            if object_hash != file_hash:
                self._s3.upload_file(str(Path(self.source).joinpath(path)), Bucket=self.dest, Key=path)
        
        for key in objects_to_delete:
            self._s3.delete_object(Bucket=self.dest, Key=key)

    def list_bucket_objects(self):
        try:
            contents = self._s3.list_objects(Bucket=self.dest)['Contents']
        except KeyError:
            # No Contents Key, empty bucket.
            self.contents = []
        else:
            self.contents = contents

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