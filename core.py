import boto3
import docker
import os
import json
from pathlib import Path
import tempfile
import time

class S3DockerManager:
    def __init__(self, config_name='default'):
        self.config = self._load_config(config_name)
        self.s3_client = self._init_s3_client()
        self.docker_client = docker.from_env()

    def _load_config(self, config_name):
        config_dir = Path.home() / '.s3docker'
        config_file = config_dir / 'configs.json'
        
        if not config_file.exists():
            raise FileNotFoundError("Configuration not found. Please run 's3docker config'")
            
        with open(config_file) as f:
            configs = json.load(f)
            
        if config_name not in configs:
            raise KeyError(f"Configuration '{config_name}' not found")
            
        return configs[config_name]

    def _init_s3_client(self):
        return boto3.Session(
            aws_access_key_id=self.config['aws_access_key_id'],
            aws_secret_access_key=self.config['aws_secret_access_key'],
            region_name=self.config['aws_region']
        ).client('s3')

    def push(self, image_name, replace=False):
        # Save image to temporary tar file
        temp_dir = tempfile.mkdtemp()
        tar_path = os.path.join(temp_dir, f"{image_name}.tar")
        
        image = self.docker_client.images.get(image_name)
        with open(tar_path, 'wb') as f:
            for chunk in image.save():
                f.write(chunk)

        # Handle existing file in S3
        s3_key = f"{self.config['s3_path']}/{image_name}.tar"
        
        try:
            if not replace:
                self.s3_client.head_object(Bucket=self.config['bucket'], Key=s3_key)
                # If file exists, move it to archive
                archive_key = f"{self.config['s3_path']}/archive/{image_name}_{int(time.time())}.tar"
                self.s3_client.copy_object(
                    Bucket=self.config['bucket'],
                    CopySource={'Bucket': self.config['bucket'], 'Key': s3_key},
                    Key=archive_key
                )
        except:
            pass  # File doesn't exist, proceed with upload

        # Upload to S3
        self.s3_client.upload_file(tar_path, self.config['bucket'], s3_key)
        
        # Cleanup
        os.remove(tar_path)
        os.rmdir(temp_dir)

    def pull(self, image_name):
        # Download from S3
        temp_dir = tempfile.mkdtemp()
        tar_path = os.path.join(temp_dir, f"{image_name}.tar")
        
        s3_key = f"{self.config['s3_path']}/{image_name}.tar"
        self.s3_client.download_file(self.config['bucket'], s3_key, tar_path)

        # Load image
        with open(tar_path, 'rb') as f:
            self.docker_client.images.load(f)

        # Cleanup
        os.remove(tar_path)
        os.rmdir(temp_dir)

    def list_images(self):
        """List all Docker images in the S3 bucket"""
        prefix = f"{self.config['s3_path']}/"
        response = self.s3_client.list_objects_v2(
            Bucket=self.config['bucket'],
            Prefix=prefix
        )
        
        images = []
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                if key.endswith('.tar') and '/archive/' not in key:
                    image_name = key[len(prefix):-4]  # Remove prefix and .tar
                    images.append({
                        'name': image_name,
                        'size': obj['Size'],
                        'last_modified': obj['LastModified']
                    })
        return images
