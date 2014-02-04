wikipedia-download
==================

Python script to download Wikipedia articles for reading. Intended for language learners: it searches the article from lang1, downloads it, and finds the translation of it in lang2.

Basically it's a stripped down version of wikipedia's print option. This script deletes: scripts, styles,
navigation links, categories, subtitle, list and links of references/bibliography (but not footnotes),
the TOC and deletes interwiki links.

You get this simple version for easier reading just the "main text", useful if you use popup dictionaries.


Syntax
---------

    wikipedia_download csv folder -f lang -t lang
    
  * ``csv``: a "comma-separated values" file. No quot characters and the delimiter is <kbd>tab</kbd>. Two columns: the first is the article's title and the second is the filename of the processed file. Example:
      
        wikipedia wiki
    
    That searches the article "wikipedia", process it and saves as wiki_lang.html. The filename it's used in both (language) resulting files.
  * ``folder``: the output folder where files are saved to
  * ``-f lang``: the language to search from (the main language). By default is 'en'
  * ``-t lang``: the language of desired translation.
   
lang codes must be the ones that Wikipedia uses, like [ISO 639](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)


Requirements
-------------

This script requires ``requests`` and ``BeautifulSoup``
