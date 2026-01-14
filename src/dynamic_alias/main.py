import sys
import os

# Add parent directory to path to allow running as script if needed, 
# though checking __package__ is better for installed packages.
# For local dev without install:
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from .cli import DynamicAliasCLI

def main():
    cli = DynamicAliasCLI()
    cli.run()

if __name__ == "__main__":
    main()
