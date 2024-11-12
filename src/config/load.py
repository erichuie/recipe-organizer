import yaml


def save_yaml_config(filename, options):
    """Save options into a yaml file"""
    result = {}
    try:
        with open(filename, 'w') as fp:
            result = yaml.safe_dump(options)
            fp.write(result)
    except Exception as exc:
        print(exc)
    return result

def load_yaml_config(filename):
    """Load yaml file in current config directory."""
    result = {}
    try:
        with open(filename, 'r') as fp:
            result = yaml.safe_load(fp.read())
    except Exception as exc:
        print(exc)

    return result or {}

def save_email_config(options):
    """Save options into email.yaml"""
    return save_yaml_config("email.yaml", options)

def load_email_config():
    """Load email.yaml"""
    return load_yaml_config("email.yaml")
