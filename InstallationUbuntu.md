# Installing fathom #

To use `fathom` you must have `python3` installed. If you want to install the package from PyPI, you will also need `setuptools` for `python3':

```
    sudo apt-get install python3-setuptools
```

After that you can run:

```
    sudo easy_install3 fathom
```

Alternatively you can download source package, unpack it, enter package directory and run:

```
    sudo python3 setup.py install
```

`fathom` library works with python 3.2. You can try using it with python 3.1, but then you need to install argparse package:

```
    sudo easy_install3 argparse
```

# Using Sqlite3 #

Sqlite3 comes with python3 itself.

# Using PostgreSQL #

To use PostgreSQL you need psycopg2 package. You can install it with `easy_install3`, but first you need `python3-dev` package:

```
    sudo apt-get install python3-dev
    sudo easy_install3 psycopg2
```

# Using MySQL #

To interface MySQL fathom uses pure python `pymysql` package. You can install with `easy_install3`, but remember to get package for `python3`:

```
    sudo easy_install3 pymysql3
```