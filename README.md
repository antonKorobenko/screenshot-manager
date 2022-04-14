# README

This is a simple screenshot manager for MacOS and Linux systems.

## How it works

- This script requests access to your Google Calendar (GC) linked to your Google Account.
- Then it get all upcoming events from your 'primary' GC for current date. When the event starts, this script will automatically create a new folder with the corresponding date, event start time and event name in the default screenshot directory (on a Mac this is usually `/Users/{your username}/Desktop/`)
- While event is taking place, all the screenshots you take will be saved in this directory, but as soon as your event ends (or you stop the program with `^ + C`), the following screenshots will be saved in the default directory again

## Usage

1. Clone this repository with: `git clone https://github.com/antonKorobenko/screenshot-manager.git`
2. `cd` to script directory with `cd screenshot_manager`
3. Install required packages with `pipenv install`
4. Activate your enviroment with `pipenv shell`
5. Go thru `PRESENTATION ABOUT «GOOGLE CALENDAR API».pdf` in this repo and initialize your own Google Cloud project and create `credentials.json` file, which then place in this directory
6. At line **18** in `main.py` enter your username `DEFAULT_SCREENSHOT_LOCATION = "/Users/**your username**/Desktop/"`
7. Now run script with `python main.py`
