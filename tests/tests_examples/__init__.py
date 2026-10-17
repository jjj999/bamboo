import importlib.util
from pathlib import Path
import sys
from types import ModuleType


ROOT = Path(__file__).parents[2]


def load_example(relative_path: str, module_name: str) -> ModuleType:
    """Load an example without executing its ``__main__`` block."""
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load example: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
