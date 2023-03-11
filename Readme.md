# [DLsite Lowest Price Watcher](https://imba-tjd.github.io/DLWatcher)

Tracks the lowest price of best sellers on https://dlsite.com.

Data is scraped via GitHub Actions and is hosted via GitHub Pages on `gh-pages` branch. `"` is escaped to `"...""..."` due to CSV limitation.

For more introduction, see `article` tag in `data_tmpl.html`.

## GreaseMonkey userscript

[![](https://wiki.greasespot.net/favicon.ico) Add userscript](https://github.com/imba-tjd/DLWatcher/raw/master/DLWatcher.user.js)

The `DLWatcher.user.js` adds *Lowest* label on detail pages if there are records in csv. The csv data is downloaded when installing so you need reinstall when you want to update.

## TODO

* extract中匹配单个tr的属性，假设网页变动后artifact_pattern匹配失败，目前会与未打折混淆
* appx分类也有排行榜了，5页，但artifact_pattern匹配Name失败，它没有`work_thumb_box_img`，考虑改用`<img src="data:image`下的alt
* 网页版添加userscript的按钮：GreaseMonkey图标不垂直居中、点击后会弹出一个空白页

## Won't fix

* 会请求一次icon，被CSP拦截。没有找到不请求的方式
