# 🐳 S3Docker

> Simplify Docker image distribution using AWS S3 storage

![S3Docker](https://github.com/Kawai-Senpai/s3Docker/blob/40e33f1830598a3351e568caa498d0f9a601dd47/Assets/S3Docker%20Thumbnail.png)

## 🎯 Why S3Docker?

Managing Docker images across multiple environments and teams can be challenging:
- Private registries can be expensive and complex to maintain
- Manual image transfer is time-consuming and error-prone
- Version management and rollbacks can be difficult

S3Docker solves these problems by:
- Using AWS S3 as a cost-effective storage solution
- Providing simple commands for image management
- Automatically handling versioning and archiving
- Supporting multiple configuration profiles for different environments

## ✨ Features

- 📦 Simple push/pull commands for Docker images
- 🔄 Automatic version archiving
- 📝 Multiple named configuration profiles
- 📊 Image listing with size and modification info
- 🧹 Automatic cleanup of temporary files
- 🔒 Secure AWS credentials management

## 🚀 Installation

```bash
pip install s3docker
```

## 📋 Prerequisites

- Python 3.6 or higher
- Docker installed and running
- AWS account with S3 access
- AWS credentials with the following permissions:
  - `s3:PutObject`
  - `s3:GetObject`
  - `s3:ListBucket`

## 🛠️ Configuration

### Initial Setup

```bash
s3docker config
```

Follow the interactive wizard to configure:
1. Profile name (e.g., 'prod', 'staging', 'default')
2. AWS Access Key ID
3. AWS Secret Access Key
4. AWS Region (default: us-east-1)
5. S3 Bucket name
6. S3 Path prefix (default: docker-images)

### Managing Multiple Profiles

List all configured profiles:
```bash
s3docker configs
```

## 📚 Usage Guide

### Pushing Images to S3

```bash
# Using default profile
s3docker push myapp:latest

# Using specific profile
s3docker push myapp:latest --to prod

# Replace existing image
s3docker push myapp:latest --replace
```

### Pulling Images from S3

```bash
# Using default profile
s3docker pull myapp:latest

# Using specific profile
s3docker pull myapp:latest --from prod
```

### Listing Available Images

```bash
# List images in default profile
s3docker list

# List images in specific profile
s3docker list --from prod
```

## 🔧 How It Works

1. **Push Operation**:
   - Saves Docker image to temporary tar file
   - If image exists in S3:
     - Moves existing image to archive folder (if --replace not used)
     - Archives include timestamps for version tracking
   - Uploads new image to S3
   - Cleans up temporary files

2. **Pull Operation**:
   - Downloads tar file from S3
   - Loads image into Docker
   - Automatically removes temporary files

3. **Configuration Storage**:
   - Configs stored in `~/.s3docker/configs.json`
   - Separate profiles for different environments
   - Secure credential storage

## 🌟 Best Practices

1. **Profile Management**:
   - Use different profiles for development/staging/production
   - Keep production credentials separate
   - Regular credential rotation

2. **Image Management**:
   - Use specific tags instead of 'latest'
   - Utilize --replace flag carefully
   - Regular cleanup of archived versions

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 License

MIT License - feel free to use and modify as needed!

## 🆘 Support

- Create an issue for bug reports
- Feature requests are welcome
- PRs accepted

## 🔮 Future Plans

- [ ] Support for image tags listing
- [ ] Bulk upload/download
- [ ] Compression options
- [ ] Image metadata support
- [ ] Integration with CI/CD pipelines

---

Made with ❤️ for the Docker community
