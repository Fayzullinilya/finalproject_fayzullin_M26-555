#!/usr/bin/env python3

from valutatrade_hub.cli.interface import CLI
import argparse
import logging
from valutatrade_hub.logging_config import setup_logging

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(level=log_level)     
    
    cli = CLI()
    cli.run()

if __name__ == "__main__":
    main()