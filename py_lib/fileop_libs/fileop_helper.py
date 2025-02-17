import import_helper as ih
import subprocess
import json
import os


def make_dir(abs_dir_path):
    try:
        os.makedirs(abs_dir_path, exist_ok=True)  # Use os.makedirs for creating directories
    except Exception as e:
        print(f"Error creating directory {abs_dir_path}: {e}")


def list_dir_contents(abs_dir_path):
    try:
        print(abs_dir_path)
        ls_outp = subprocess.run(["ls", abs_dir_path], capture_output=True, check=True)
        ls_str = ls_outp.stdout.decode().strip()
        return ls_str.split('\n') if ls_str else []
    except subprocess.CalledProcessError as e:
        print(f"Error listing directory contents: {e}")
        return []


def rm_dir(abs_dir_path):
    try:
        subprocess.run(["rm", "-rf", abs_dir_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error removing directory {abs_dir_path}: {e}")


def write_file(abs_file_path, content, content_type="text"):
    try:
        with open(abs_file_path, 'w') as f:
            if content_type == "text":
                f.write(content)
            elif content_type == "json" and isinstance(content, dict):
                json.dump(content, f)
            else:
                raise ValueError("Unrecognized Content Type")
    except Exception as e:
        print(f"Error writing to file {abs_file_path}: {e}")


def read_file(abs_file_path, content_type="text"):
    try:
        with open(abs_file_path, 'r') as f:
            if content_type == "text":
                return f.read()
            elif content_type == "json":
                return json.load(f)
            else:
                raise ValueError("Unrecognized Content Type")
    except Exception as e:
        print(f"Error reading file {abs_file_path}: {e}")
        return None