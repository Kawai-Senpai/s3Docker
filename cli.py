import click
import json
from pathlib import Path
from .core import S3DockerManager

def load_configs():
    config_dir = Path.home() / '.s3docker'
    config_file = config_dir / 'configs.json'
    if config_file.exists():
        with open(config_file) as f:
            return json.load(f)
    return {}

def save_configs(configs):
    config_dir = Path.home() / '.s3docker'
    config_dir.mkdir(exist_ok=True)
    with open(config_dir / 'configs.json', 'w') as f:
        json.dump(configs, f, indent=2)

@click.group()
def cli():
    """S3Docker - Manage Docker images using S3 storage"""
    pass

@cli.command()
def config():
    """Configure a new S3Docker profile"""
    configs = load_configs()
    
    click.echo("S3Docker Configuration Wizard")
    click.echo("-" * 30)
    
    # Get profile name
    while True:
        name = click.prompt(
            "\nEnter profile name (leave empty for 'default')",
            default='default'
        )
        if name in configs:
            if not click.confirm(f"Profile '{name}' already exists. Overwrite?"):
                continue
        break
    
    config = {}
    click.echo(f"\nConfiguring profile: {click.style(name, fg='green')}")
    click.echo("Enter your AWS credentials and settings:")
    config['aws_access_key_id'] = click.prompt("  AWS Access Key ID")
    config['aws_secret_access_key'] = click.prompt("  AWS Secret Access Key")
    config['aws_region'] = click.prompt("  AWS Region", default="us-east-1")
    config['bucket'] = click.prompt("  S3 Bucket name")
    config['s3_path'] = click.prompt("  S3 Path prefix", default="docker-images")

    configs[name] = config
    save_configs(configs)
    click.echo(f"\n✨ Configuration '{name}' saved successfully!")

@cli.command()
def configs():
    """List all available configurations"""
    configs = load_configs()
    if not configs:
        click.echo("No configurations found. Create one using 's3docker config'")
        return
    
    click.echo("\nAvailable configurations:")
    click.echo("-" * 30)
    for name in configs:
        config = configs[name]
        click.echo(f"\n{click.style(name, fg='green')}:")
        click.echo(f"  Region: {config['aws_region']}")
        click.echo(f"  Bucket: {config['bucket']}")
        click.echo(f"  Path: {config['s3_path']}")

@cli.command()
@click.option('--from', 'from_', default='default', help='Configuration to use')
def list(from_):
    """List all Docker images in S3"""
    try:
        manager = S3DockerManager(from_)
        images = manager.list_images()
        
        if not images:
            click.echo(f"No images found in configuration '{from_}'")
            return
            
        click.echo(f"\nDocker images in '{from_}' configuration:")
        click.echo("-" * 50)
        
        for img in images:
            size_mb = img['size'] / (1024 * 1024)
            modified = img['last_modified'].strftime('%Y-%m-%d %H:%M:%S')
            click.echo(f"\n{click.style(img['name'], fg='green')}")
            click.echo(f"  Size: {size_mb:.1f} MB")
            click.echo(f"  Modified: {modified}")
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

@cli.command()
@click.argument('image_name')
@click.option('--to', default='default', help='Configuration to use')
@click.option('--replace', is_flag=True, help='Replace existing image in S3')
def push(image_name, to, replace):
    """Push a Docker image to S3"""
    try:
        manager = S3DockerManager(to)
        manager.push(image_name, replace)
        click.echo(f"Successfully pushed {image_name} to S3 using '{to}' config")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

@cli.command()
@click.argument('image_name')
@click.option('--from', 'from_', default='default', help='Configuration to use')
def pull(image_name, from_):
    """Pull a Docker image from S3"""
    try:
        manager = S3DockerManager(from_)
        manager.pull(image_name)
        click.echo(f"Successfully pulled {image_name} from S3 using '{from_}' config")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

if __name__ == '__main__':
    cli()
