import sys
from rich.console import Console
from rich.table import Table

console = Console()

if len(sys.argv) > 1:
    command = sys.argv[1]
    if command == "table":
        # Expecting pairs of file and status after 'table'
        data = sys.argv[2:]
        table = Table(title="[bold]Carga de Firmware[/bold]", border_style="green", title_align="left")
        table.add_column("Archivo", style="cyan", no_wrap=True)
        table.add_column("Estado", style="magenta")

        for i in range(0, len(data), 2):
            table.add_row(data[i], data[i+1])
        
        console.print(table)
    else:
        # Treat other arguments as messages to print
        console.print(" ".join(sys.argv[1:]))