import csv
import logging
import os
import re
import time
import urllib3
from datetime import date
from typing import NamedTuple, Iterable

pattern = re.compile(
    'id="_link_([^"]+?)"'  # RJCode
    '.+?'
    'work_thumb_box_img" alt="([^"]+?)"'  # Name
    '.+?'
    'work_price discount">([^<]+?)<'  # Price
    '.+?'
    'type_sale">(.+?)%OFF', re.S)  # Discount percent

logger = logging.Logger(__name__)


class Artifact(NamedTuple):
    ID: str
    Name: str
    Price: str
    Discount: int
    Date: date


ArtifactDict = dict[str, Artifact]


def get_data() -> ArtifactDict:
    '''获得各个分类的top商品'''
    entries = []
    for cat in ('comic', 'game', 'voice'):
        for page in range(1, 6):
            html = download('https://www.dlsite.com/maniax/ranking/total?sort=sale&category=%s&page=%d' % (cat, page))
            entries += pattern.findall(html)

    for cat in ('books', 'girls'):
        for page in range(1, 3):
            html = download('https://www.dlsite.com/%s/ranking/total?page=%d' % (cat, page))
            entries += pattern.findall(html)

    for cat in ('books', 'girls'):
        for page in range(1, 4):
            html = download('https://www.dlsite.com/%s/ranking/total?page=%d' % (cat, page))
            entries += pattern.findall(html)

    assert entries  # 假定总有打折的，如果为空说明pattern出了问题
    today = date.today()
    logger.info('download end.')
    logger.debug('entries:', entries)
    return {entry[0]: Artifact(entry[0], entry[1], entry[2], int(entry[3]), today) for entry in entries}


def download(url: str) -> str:
    global pm
    pm = globals().get('pm') or urllib3.PoolManager(headers={'Accept-Encoding': 'gzip'})

    logger.info('downloading', url)
    resp = pm.request('GET', url)
    html = resp.data.decode()
    logger.debug(html)
    time.sleep(0.5)
    return html


def save(data: Iterable[Artifact], dbname='data.csv'):
    with open(dbname, 'w+', encoding='u8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(('ID', 'Name', 'Price', 'Discount', 'Date'))
        writer.writerows(data)


def load(dbname='data.csv') -> list[Artifact]:
    if not os.path.exists(dbname):
        return []

    with open(dbname, encoding='u8', newline='') as f:
        f.readline()  # 去掉header
        return [Artifact(x[0], x[1], x[2], int(x[3]), date.fromisoformat(x[4])) for x in csv.reader(f)]


def merge(old: list[Artifact], new: ArtifactDict):
    '''因为数据源只跟踪最新的top榜，所以把老的数据合并到新的数据中'''
    logger.info('merging...')
    for item in old:
        if (id := item.ID) in new and item.Discount > new[id].Discount:
            new[id] = item
    logger.debug('new entries:', new)


def ya_api_builder(ids: list[str]):
    '''Yet another api. Chunk in 100.'''
    from itertools import islice
    endpoint = 'https://www.dlsite.com/maniax/product/info/ajax?cdn_cache_min=1&product_id='
    while slice := tuple(islice(ids, 100)):
        yield endpoint + '%2C'.join(slice)


def ya_api_builder_2(n=100):
    '''Yet another api. Get game by sales. The data contains free artifacts.'''
    return 'https://www.dlsite.com/maniax/sapi/=/sex_category/+/order/dl_d/work_type_category/game/per_page/%d/format/json/?cdn_cache=1' % n


def make_html(data: Iterable[Artifact]):
    with open('data_tmpl.html', encoding='u8') as f:
        html_tmpl = f.read()
    row_tmpl = '<tr><td>{0}</td><td><a target="_blank" href="https://www.dlsite.com/maniax/work/=/product_id/{0}.html">{1}</a></td><td>{2}</td><td>{3}%</td><td><time>{4}</time></td></tr>'
    rows = ''.join((row_tmpl.format(*x) for x in data))
    html = html_tmpl.replace('{DATA}', rows)
    html = re.sub(r'\n\s*',' ',html)
    with open('data.html', 'w+', encoding='u8') as out:
        out.write(html)


def make_html_from_csv():
    '''for testing'''
    make_html(load())


def main():
    logging.basicConfig(format='%(asctime)s - %(levelname)s:%(message)s', level='INFO')

    old = load()
    new = get_data()
    merge(old, new)

    datalist = list(sorted(new.values(), key=lambda x: x[0]))
    save(datalist)
    print('record counts:', len(new))
    make_html(datalist)


if __name__ == '__main__':
    main()
