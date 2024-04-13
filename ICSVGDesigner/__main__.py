import argparse
from ICSVGDesigner import ICSVGDesigner
import pathlib

def cli():
    app = ICSVGDesigner()
    iconpath = pathlib.Path(__file__).parent / 'icon.ico'
    if iconpath.exists():
        app.iconbitmap(iconpath)
    app.mainloop()

if __name__ == "__main__":
    cli()