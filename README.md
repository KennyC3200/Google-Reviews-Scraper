# Reviews Scraper
This is a simple script used for the purposes of scraping Google reviews. The reviews are parsed and written into
a JSON file.

Usage
-----
1. Install `virtualenv` via `pip`. E.g `python3 -m pip install virtualenv`
2. Source the venv. E.g `source <venv>/bin/activate`
3. Install the dependencies. E.g `python3 -m pip install -r requirements.txt`
4. Run the venv. E.g `<venv>/bin/python src/ramsay.py`
5. The output file will be in the `/out` folder. It takes in a file called `restuarants.csv`, where it is the restaurant's name followed by the URL

TODO
-----
* Add more fields (like sort by date, name, etc.)
    * Click the sort by newest button
