# Reviews Scraper
This is a simple script used for the purposes of scraping Google reviews. The reviews are parsed and written into
a JSON file.

Usage
-----
1. Install `virtualenv` via `pip`. `python3 -m pip install virtualenv`
2. Source the venv. `source <venv>/bin/activate`
3. Install the dependencies. `python3 -m pip install -r requirements.txt`
4. Run the venv. `<venv>/bin/python src/ramsay.py`

TODO
-----
* Maybe switch to data oriented design instead
* Add more fields (like sort by date, name, etc.)
    * Click the sort by newest button
