"""Allow `python -m tradingagents.engine` to dispatch to the typer CLI."""

from tradingagents.engine.cli import main

if __name__ == "__main__":
    main()
