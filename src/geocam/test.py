from pathlib import Path
directory = Path(__file__).absolute()
newname = directory.name.rsplit(".", 1)[0]
index_text = f"¯\\_(ツ)_/¯ \nNO CORNER WERE FOUND \nPLEASE CHANGE THE FOCUS"
print(index_text)