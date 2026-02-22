# Setup Guide (Windows)

## 1. Install Python

Download and run the installer from https://www.python.org/downloads/

**Important:** Check "Add Python to PATH" during installation.

Open Command Prompt and verify:

```
python --version
```

## 2. Download the Project

Copy the `dad_flight_agent` folder to your computer (e.g. `C:\Users\YourName\dad_flight_agent`).

Open Command Prompt and navigate to it:

```
cd C:\Users\YourName\dad_flight_agent
```

## 3. Install Dependencies

```
pip install -r requirements.txt
```

## 4. Run a Search

```
python main.py --start-date 2026-05-01 --end-date 2026-05-31
```

Results will be saved to `runs\<today's date>\run_1\`:
- `flights_report.xlsx` - formatted Excel report with top 5 per destination
- `flights_filtered.csv` - all round-trip combinations sorted by price

You can Ctrl+C to stop and re-run the same command later - it picks up where it left off.
