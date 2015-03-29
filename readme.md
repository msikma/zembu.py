zembu.py
========

Simple script that runs through a list of words and checks Whois to see if the
words are available as domain names.


Usage
-----

Type `./zembu.py --help` for the following prompt:

````
usage: zembu.py [-h] [-V] --dict DICT [--tlds TLDS] [--verbose]
                [--log-file LOG_FILE]

zembu.py: checks all entries in a list of words for domain availability

optional arguments:
  -h, --help           Show this help message and exit.
  -V, --version        Show version number and exit.
  --dict DICT          Path to the dictionary file to use. Must contain one
                       word per line.
  --tlds TLDS          Top-level domain to check, e.g. "com,net" to check
                       "<word>.com" and "<word>.net". (Default: "com")
  --verbose            Outputs all Whois commands we run. (Default: False)
  --log-file LOG_FILE  Saves a list of all available domain names to a text
                       file. (Default: "zembu_output.log")
````
Only `--dict` is a required argument.



Unix dictionary
---------------
If you're on a Unix-like system, you can use the internal dictionary. It's
usually found at `/usr/share/dict/words` or `/usr/dict/words`.


License
-------

MIT license.
