import boto3
import docker
import os
import json
from pathlib import Path
import tempfile
import time
import uuid
import ultraprint.common as p
from tqdm import tqdm

class S3DockerManager:
    def __init__(self, config_name='default', temp_dir=None):
        self.config = self._load_config(config_name)
        self.s3_client = self._init_s3_client()
        self.docker_client = docker.from_env()
        self.temp_dir = temp_dir

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

    def _create_temp_dir(self):
        if self.temp_dir:
            # Create a random named directory within specified temp_dir
            tmp_path = Path(self.temp_dir) / f"s3docker-{uuid.uuid4().hex[:8]}"
            tmp_path.mkdir(parents=True, exist_ok=True)
            return str(tmp_path)
        return tempfile.mkdtemp()

    def _get_file_size(self, image):
        """Get total size of Docker image tar"""
        size = 0
        for chunk in image.save(named=True):
            size += len(chunk)
        return size

    def push(self, image_name, replace=False):
        # Create temporary directory
        temp_dir = self._create_temp_dir()
        tar_path = os.path.join(temp_dir, f"{image_name}.tar")
        
        try:
            p.cyan("📦 Preparing Docker image...")
            image = self.docker_client.images.get(image_name)
            total_size = self._get_file_size(image)

            with open(tar_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc="Saving image") as pbar:
                    for chunk in image.save(named=True):
                        f.write(chunk)
                        pbar.update(len(chunk))

            # Handle existing file in S3
            s3_key = f"{self.config['s3_path']}/{image_name}.tar"
            
            try:
                if not replace:
                    p.yellow("🔍 Checking for existing image...")
                    self.s3_client.head_object(Bucket=self.config['bucket'], Key=s3_key)
                    # If file exists, move it to archive
                    archive_key = f"{self.config['s3_path']}/archive/{image_name}_{int(time.time())}.tar"
                    p.blue("📁 Archiving existing image...")
                    self.s3_client.copy_object(
                        Bucket=self.config['bucket'],
                        CopySource={'Bucket': self.config['bucket'], 'Key': s3_key},
                        Key=archive_key
                    )
            except:
                pass  # File doesn't exist, proceed with upload

            p.cyan("☁️ Uploading to S3...")
            file_size = os.path.getsize(tar_path)
            with tqdm(total=file_size, unit='B', unit_scale=True, desc="Uploading") as pbar:
                self.s3_client.upload_file(
                    tar_path,
                    self.config['bucket'],
                    s3_key,
                    Callback=lambda bytes_transferred: pbar.update(bytes_transferred)
                )
        finally:
            p.blue("🧹 Cleaning up temporary files...")
            try:
                os.remove(tar_path)
                os.rmdir(temp_dir)
            except:
                pass  # Best effort cleanup

    def pull(self, image_name):
        # Create temporary directory
        temp_dir = self._create_temp_dir()
        tar_path = os.path.join(temp_dir, f"{image_name}.tar")
        
        try:
            s3_key = f"{self.config['s3_path']}/{image_name}.tar"
            
            # Get file size for progress bar
            p.cyan("📊 Getting image information...")
            obj = self.s3_client.head_object(Bucket=self.config['bucket'], Key=s3_key)
            file_size = obj['ContentLength']

            p.cyan("☁️ Downloading from S3...")
            with tqdm(total=file_size, unit='B', unit_scale=True, desc="Downloading") as pbar:
                self.s3_client.download_file(
                    self.config['bucket'],
                    s3_key,
                    tar_path,
                    Callback=lambda bytes_transferred: pbar.update(bytes_transferred)
                )

            p.cyan("🐳 Loading image into Docker...")
            with open(tar_path, 'rb') as f:
                total_size = os.path.getsize(tar_path)
                with tqdm(total=total_size, unit='B', unit_scale=True, desc="Loading image") as pbar:
                    for response in self.docker_client.images.load(f):
                        if 'id' in response:
                            pbar.update(total_size)  # Update on successful load
        finally:
            p.blue("🧹 Cleaning up temporary files...")
            try:
                os.remove(tar_path)
                os.rmdir(temp_dir)
            except:
                pass  # Best effort cleanup

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
