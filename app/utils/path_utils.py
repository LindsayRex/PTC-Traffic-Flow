# app/utils/path_utils.py
import os
import sys
from pathlib import Path
from typing import Union, Optional

# Get the project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def ensure_project_root_in_path():
    """
    Ensures that the project root directory is in sys.path.
    """
    project_root_str = str(PROJECT_ROOT)
    if project_root_str not in sys.path:
        sys.path.append(project_root_str)
        return True
    return False

def get_project_root() -> Path:
    """
    Returns the project root Path object.
    
    Returns:
        pathlib.Path: The project root directory
    """
    return PROJECT_ROOT

def get_app_root() -> Path:
    """
    Returns the app directory Path object.
    
    Returns:
        pathlib.Path: The app directory
    """
    return PROJECT_ROOT / 'app'

def get_data_path(filename: Optional[str] = None) -> Path:
    """
    Returns the path to the data directory or a specific file within it.
    
    Args:
        filename (str, optional): The name of a file in the data directory.
    
    Returns:
        pathlib.Path: Path to the data directory or specific file
    """
    data_dir = get_app_root() / 'data'
    return data_dir / filename if filename else data_dir

def normalize_path(path: Union[str, Path], relative_to: Optional[Path] = None) -> Path:
    """
    Normalizes a path to an absolute path, optionally relative to a given directory.
    
    Args:
        path (Union[str, Path]): The path to normalize
        relative_to (Path, optional): Directory to resolve relative paths against.
                                     Defaults to PROJECT_ROOT.
    
    Returns:
        pathlib.Path: The normalized absolute path
    """
    if relative_to is None:
        relative_to = PROJECT_ROOT
        
    path_obj = Path(path)
    
    # If it's already absolute, return it
    if path_obj.is_absolute():
        return path_obj
        
    # Handle paths that start with app/
    if str(path_obj).startswith('app/') or str(path_obj).startswith('app\\'):
        return PROJECT_ROOT / path_obj
        
    # Otherwise, resolve against the specified base
    return relative_to / path_obj