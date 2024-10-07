import toml

def load_config(file_path):
    return toml.load(file_path)
