# CTMR list scanning application
A small GUI wrapper over an SQLite3-backed list scanning tool.

## Development
Please refer to the [fbs manual](https://build-system.fman.io/manual/) for details on how
to work with `fbs`. 

### Dependencies
The repo contains [conda environment files](https://conda.io/docs/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file) to
build a suitable development environment on both Windows and Linux. 
The code structure is based on the template provided by [fman build system (fbs)](https://build-system.fman.io/).
Below are the main dependencies and their tested versions listed.

- pandas (0.23.4) -- To easily read CSV and Excel into tables
- xlrd (1.1.0) -- Required for Excel functionality of Pandas
- pyqt5 (5.9.2) -- Recommended version for use with fbs
- fbs (0.1.7) -- The fman build system, use to create cross-platform installable packages

The conda development environment files also contain
[rope](https://github.com/python-rope/rope) and
[pylint](https://www.pylint.org/) to simplify development a bit.

### Running 
To run the program when developing, activate the environment and call `python -m fbs run`.

### Freezing
To freeze the package into a "folder"-style distribution, call `python -m fbs freeze`. 

### Create installer
To create an installer, call `python -m fbs installer`. Note that this
requires [NSIS](http://nsis.sourceforge.net/Main_Page) on Windows.


## Artwork credits
Scanner icons made by [Freepik](http://www.freepik.com) from [Flaticon](https://www.flaticon.com/) is licensed by [Creative Commons BY 3.0](http://creativecommons.org/licenses/by/3.0/).

CTMR and bacteria artwork by [Ina Schuppe Koistinen](http://www.inasakvareller.se/). Used with permission.