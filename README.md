# Sun and rain: the UK's sunshine against its rainfall

Every 1 km square of the United Kingdom placed by its sunshine and its rainfall at once, from the Met Office's HadUK-Grid thirty-year averages for 1961 to 1990 and 1991 to 2020. The interactive page lets you switch between the year, any season or any month, move the class breaks (or use equal shares of land), compare the two periods with the same breaks, light up any one colour of the key, look up a place or postcode for its monthly sunshine, rain and daytime highs, find squares with weather like yours, count the pleasantly warm months, and rank the sunniest and wettest towns.

**Interactive version:** https://tristan-hotham.github.io/sun-and-rain-uk/

**Paper and archived release:** https://doi.org/10.5281/zenodo.23732582

A data study by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349).

## Headline results

- In 1991 to 2020 the average UK land square got 1,403 hours of bright sunshine and 1,162 mm of rain a year. Sunshine runs from 1,992 hours at Dungeness to 784 on the summit of Ben Nevis; rain from 493 mm on the Isle of Sheppey to 4,796 mm at the head of Borrowdale. (One coastal square at the mouth of the Tees has 469 mm, but its neighbours average 599 mm, so I treat it as a gridding artefact.)
- Sunshine and rainfall are tightly opposed: Spearman's rank correlation across the 245,077 squares is −0.72.
- With classes at the terciles of the land, sunny and dry covers 21% of the UK (51,389 km², mostly East of England, South East and East Midlands) and dull and wet 24% (58,762 km², three quarters in Scotland). Sunny and wet covers 1.9% (4,651 km², mostly Cornwall and Devon, then Carmarthenshire and Pembrokeshire) and dull and dry 0.2% (608 km², around the Moray Firth).
- The towns of the sunny and dry class hold 49% of the population of UK towns of 15,000 or more (GeoNames).
- 80% of the sunniest 1% of squares lie within 5 km of the sea, against 19% of Great Britain's land. Within England, the first 2 km of coast get 1,684 hours a year against 1,505 more than 20 km inland.
- From 1961 to 1990 to 1991 to 2020 the UK became 5.6% sunnier (+75 hours) and 7.2% wetter (+79 mm); 90% of the land became both. England gained 7.5% in sunshine, Northern Ireland 1.8%; the North East (11.1%) and East Midlands (10.1%) gained most. With fixed breaks, the sunniest class grew from 26,992 to 81,886 km².
- May is the sunniest month in 72% of squares; December is the UK's dullest and wettest month on average.
- Sunniest towns of 15,000 or more: Folkestone (1,937 hours), Sandown, Dover. Dullest and wettest: Fort William (927 hours, 2,405 mm). Driest: Southend-on-Sea (526 mm).

Every number is in `data/results.json`, which the page, paper, blog and collage are built from.

## Files

| Path | What it is |
|---|---|
| `index.html` | The interactive page. Results are embedded; the grids, towns and place names are loaded from `data/`. |
| `header.png` | Social card (1200 by 630). |
| `data/grid/*.png` | The page's grids, 8-bit quantised PNGs cropped to the UK (660 by 1,214 pixels of 1 km; `meta.json` gives the window and the decoding formulas): `ann9120.png` and `ann6190.png` (R sunshine, G rainfall, B annual mean daily maximum temperature for 1991 to 2020), `change.png` (R and G: percentage change in sunshine and rainfall), `m01.png` to `m12.png` (monthly 1991 to 2020: R sunshine, G rainfall, B maximum temperature) and `regions.png` (region codes, see `data/regions_key.json`). |
| `data/cells_5km.csv` | 5 km averages of every layer (annual sunshine and rainfall for both periods; monthly sunshine, rainfall and maximum temperature for 1991 to 2020), with land area and region, in British National Grid kilometres. |
| `data/towns.csv` | Climate of the 803 UK GeoNames places of 15,000 or more and the 1,426 OS Open Names cities and towns: annual and monthly values, both periods, region. |
| `data/regions.csv` | Means and changes for each nation and English region. |
| `data/coast_bands.csv` | Sunshine and rainfall by distance from the sea (Great Britain). |
| `data/towns_page.json`, `data/places_search.json` | Compact town table and place-name list for the page. |
| `data/coast_bng.json` | Natural Earth land (public domain) projected to British National Grid, for context. |
| `data/results.json` | Every number used anywhere. |
| `code/haduk.py` | Reads the HadUK-Grid NetCDF files in place; the page's quantisation. |
| `code/palette.py` | The bivariate palette (four corners mixed in CIELAB). |
| `code/01_prepare.py` | Page grids, regions, places, towns and the 5 km table. |
| `code/02_analyse.py` | All statistics; writes `results.json`, `regions.csv`, `coast_bands.csv`. |
| `code/03_build_site.py` | Fills `code/page_template.html` to make `index.html` and checks facts stated in words. |
| `code/04_header.py`, `code/05_figures.py`, `code/figlib.py` | Social card and static figures (matplotlib). |
| `code/06_paper.py` | Builds the paper PDF from `code/paper_template.tex` with xelatex. |
| `code/07_release.py` | Blog post, blog and Zenodo metadata, Zenodo folder. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `release/` | Paper PDF and source, blog post and figures, Zenodo files. |

## Method in brief

- **Data.** HadUK-Grid v1.3.2.ceda 1 km thirty-year averages: annual sunshine hours and rainfall for 1961 to 1990 and 1991 to 2020; monthly sunshine, rainfall and mean daily maximum temperature for 1991 to 2020. 245,077 land squares on the British National Grid.
- **Classes.** Terciles of the land (each square one km²) for each measure, crossed into nine classes (quartiles and sixteen classes as an option on the page). For 1991 to 2020 the breaks are 1,310 and 1,526 hours, and 817 and 1,231 mm. Then and now uses the 1991 to 2020 breaks for both periods.
- **Places.** Regions from the nearest OS Open Names place; Northern Ireland is the land block containing Belfast. Towns take the mean of the land squares in the 3 km block around their point (GeoNames places of 15,000 or more, excluding sections of other places; OS Open Names cities and towns).
- **Coast.** Distance from each square's centre to the nearest non-land cell, Great Britain only.
- **Page encoding.** Annual sunshine in 6 hour steps, rainfall on a log scale (under 1% error), monthly sunshine in 1.2 hour steps, temperature in eighths of a degree. Text numbers come from the full-precision data.

## Known limits

- HadUK-Grid interpolates between stations with geographic predictors; values in remote hills rest on few stations and are model estimates.
- Sunshine instruments and the station network changed between the periods, so part of the change may be instrumental; the change map shows round patches centred on single stations.
- Thirty-year averages hide year-to-year variability. Town values are for a 3 km block around a point. GeoNames populations are approximate and of mixed date.

## How to rerun

Inputs are read in place from the paths at the top of each script: the seven HadUK-Grid NetCDF files (`HADUK_DIR`), OS Open Names (`osnames_gb.tsv`, compact), GeoNames `cities15000.zip` and Natural Earth 1:10m land.

```
python3 code/01_prepare.py
python3 code/02_analyse.py
python3 code/03_build_site.py
FONT_DIR=path/to/fonts python3 code/04_header.py
FONT_DIR=path/to/fonts python3 code/05_figures.py
python3 code/06_paper.py
python3 code/07_release.py
```

Needs Python 3 with numpy, pandas, scipy, h5py, pyproj, shapely, Pillow and matplotlib, and xelatex with TeX Gyre Pagella and Inter for the paper.

## Sources and licences

- Climate: Met Office; Hollis, D.; McCarthy, M.; Kendon, M.; Legg, T. (2026): HadUK-Grid Gridded Climate Observations on a 1km grid over the UK, v1.3.2.ceda (1836 to 2025). NERC EDS Centre for Environmental Data Analysis. https://catalogue.ceda.ac.uk/uuid/789b3065d74a4c948ab05d33556c86d0. Contains Met Office data © Crown copyright 2026, Open Government Licence v3.
- Places: OS Open Names, contains OS data © Crown copyright and database right 2026 (Open Government Licence v3.0); GeoNames cities15000 (CC BY 4.0).
- Context land: Natural Earth (public domain). Postcode lookups on the page: postcodes.io (ONS and OS open data). Map library: Leaflet.

The data files are released under the Open Government Licence v3 (see `LICENSE`). Text and figures: CC BY 4.0. Code: MIT.

## Citation

Hotham, T. (2026) Sun and Rain: The United Kingdom's Sunshine Against Its Rainfall at 1 km, 1961 to 2020. Zenodo. https://doi.org/10.5281/zenodo.23732582

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
