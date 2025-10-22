# Load Data

1. Change `YEAR` to be the desired year in `main.py`
2. Add your `.env` credentials
3. Run the script

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
