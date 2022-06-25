# DLsite Lowest Price Watcher

Tracks the lowest price of best sellers on https://dlsite.com.

Data is crawled via GitHub Actions and is hosted via GitHub Pages on `gh-pages` branch.

For more introduction, see `article` tag in `data_tmpl.html`.

TODO:

* GreaseMonkey script
* There are some html entities in csv：`&amp; &lt; &gt;` because it's unclear how to encode them in *make_html*, and `"` is escaped to `"...""..."`
