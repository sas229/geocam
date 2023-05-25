from pathlib import Path
directory = Path(__file__).absolute()
newname = directory.name.rsplit(".", 1)[0]
print(newname)