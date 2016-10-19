# gfinance
A web scraper of Google Finance, that stores the data in a MongoDB database.

The function `google_sector_report` in `scraper.py` returns a JSON containing the sector summary on the Google Finance page (www.google.com/finance).

To get the data for the Healthcare sector for example, one should run
```python
dict=google_sector_report()
dict['result']['Healthcare']
```

Each sector records its top movers (gainer and loser) and their change:
```python
dict=google_sector_report()
print("The sector move of Healtcare:")
dict['result']['Healthcare']['change']
print("The move of the biggest gainer of Technology:")
dict['result']['Technology']['biggest_gainer']['change']
```