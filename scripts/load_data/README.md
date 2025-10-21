# Load Data

1. Create `input/` directory
2. Put the unzipped `.txt` file into it
3. Change the year and input file in `main.py`
4. Run the script

## uv

### Installing Dependencies

```
uv sync
# Windows
source .venv/Scripts/activate
# MacOS
source .venv/bin/activate
```

### Running the file

```
uv run main.py
```

## pip

### Installing Dependencies

```
python -m venv .venv
# Windows
source .venv/Scripts/activate
# MacOS
source .venv/bin/activate
pip install -r requirements.txt
```

### Running the file

```
python main.py
```
