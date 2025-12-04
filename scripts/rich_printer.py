#!/usr/bin/env python3
import sys
from rich.console import Console
from rich.table import Table

def main():
    console = Console()

    if len(sys.argv) < 2:
        return

    # If the first argument is "table", create a table
    if sys.argv[1] == "table" and len(sys.argv) > 2:
        table = Table(show_header=True, header_style="bold magenta", border_style="dim")
        table.add_column("File", style="cyan", width=30)
        table.add_column("Status")

        # Arguments come in pairs: file, status
        args = sys.argv[2:]
        for i in range(0, len(args), 2):
            if i + 1 < len(args):
                table.add_row(args[i], args[i+1])
        
        console.print(table)
    else:
        # Otherwise, print formatted text
        console.print(" ".join(sys.argv[1:]))

if __name__ == "__main__":
    main()