import os
from pathlib import Path
from bisect import bisect_left
import boto3

class S3Sync:

    def __init__(self):
        self._s3 = boto3.client('s3',
                                endpoint_url='http://storage:9000',
                                aws_access_key_id=os.environ['MINIO_ACCESS_KEY'],
                                aws_secret_access_key=os.environ['MINIO_SECRET_KEY'])

    def sync(self, source, dest):
        paths = self.list_source_objects(source_folder=source)
        objects = self.list_bucket_objects(dest)

        # Getting the keys and ordering to perform binary search
        # each time we want to check if any paths is already there.
        object_keys = [obj['Key'] for obj in objects]
        object_keys.sort()
        object_keys_length = len(object_keys)

        for path in paths:
            # Binary search.
            index = bisect_left(object_keys, path)
            if index == object_keys_length:
                # If path not found in object_keys, it has to be sync-ed.
                self._s3.upload_file(str(Path(source).joinpath(path)),  Bucket=dest, Key=path)

    def list_bucket_objects(self, bucket):
        try:
            contents = self._s3.list_objects(Bucket=bucket)['Contents']
        except KeyError:
            # No Contents Key, empty bucket.
            return []
        else:
            return contents

    @staticmethod
    def list_source_objects(source_folder):
        path = Path(source_folder)

        paths = []

        for file_path in path.rglob("*"):
            if file_path.is_dir():
                continue
            str_file_path = str(file_path)
            str_file_path = str_file_path.replace(f'{str(path)}/', "")
            paths.append(str_file_path)

        return paths