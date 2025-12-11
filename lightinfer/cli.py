import argparse
import importlib
import os
import sys

from lightinfer.server import LightServer, logger


def load_class(path: str):
    """Dynamically load a class from a module path string.

    Format: module:Class or module.path:Class
    Example: my_model:MyModel
    """
    try:
        if ":" not in path:
            print("Error: Import path must be in 'module:Class' format.")
            sys.exit(1)

        module_path, class_name = path.split(":", 1)

        # Ensure current directory is in python path
        cwd = os.getcwd()
        if cwd not in sys.path:
            sys.path.insert(0, cwd)

        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        return cls
    except ImportError as e:
        print(f"Error: Could not import module '{module_path}'. {e}")
        sys.exit(1)
    except AttributeError:
        print(f"Error: Class '{class_name}' not found in module '{module_path}'.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading class: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="LightInfer: Serve your models instantly."
    )
    parser.add_argument(
        "model",
        help="The model class to serve in 'module:Class' format (e.g., model:MyModel)",
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to listen on (default: 8000)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker threads (model instances) to spawn (default: 1)",
    )

    args = parser.parse_args()

    # Load the model class
    logger.info(f"Loading model class: {args.model}")
    ModelClass = load_class(args.model)

    # Instantiate workers
    workers = []
    logger.info(f"Instantiating {args.workers} worker(s)...")
    try:
        # We assume the model class can be instantiated without arguments
        # If arguments are needed, users should wrap it or use a factory class/method
        # For a simple CLI, 0-arg init is standard expectation.
        for i in range(args.workers):
            workers.append(ModelClass())
    except Exception as e:
        print(f"Error instantiating model: {e}")
        sys.exit(1)

    # Start Server
    server = LightServer(workers)
    server.start(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
