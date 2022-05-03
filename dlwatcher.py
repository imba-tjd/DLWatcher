import csv
import logging
import os
import re
import time
import urllib3
from datetime import date
from typing import NamedTuple, Iterable

tr_pattern = re.compile('<tr[^>]*>(.+?)</tr>', re.S)
artifact_pattern = re.compile(
    'id="_link_([^"]+?)"'  # RJCode
    '.+?'
    'work_thumb_box_img" alt="([^"]+?)"'  # Name
    '.+?'
    'work_price discount">([^<]+?)<'  # Price
    '.+?'
    'type_sale">(.+?)%OFF', re.S)  # Discount percent

logger = logging.getLogger(__name__)
pm = urllib3.PoolManager(headers={'Accept-Encoding': 'gzip'}, timeout=10)
today = date.today()


class Artifact(NamedTuple):
    ID: str
    Name: str
    Price: int
    Discount: int
    Date: date


class Overview(NamedTuple):
    Count: int
    P25: int
    P50: int
    P75: int
    Avg: int


ArtifactDict = dict[str, Artifact]


def ArtifactIter2Dict(entries: Iterable[Artifact]) -> dict[str, Artifact]:
    return {entry[0]: entry for entry in entries}


def get_data() -> Iterable[Artifact]:
    '''获得各个分类的top商品'''
    for cat in ('comic', 'game', 'voice'):
        yield from get_data2(('maniax',), range(1, 6), cat)

    yield from get_data2(('books', 'girls', 'bl'), range(1, 3))
    yield from get_data2(('home', 'pro'), range(1, 4))
    yield from get_data2(('comic',), range(1, 2))

    logger.info('download ends.')


def get_data2(cats: Iterable[str], pages: range, cat2: str = '') -> Iterable[Artifact]:
    '''maniax的分类在cat2里，其余的分类在cats里'''
    for cat in cats:
        for page in pages:
            url = 'https://www.dlsite.com/%s/ranking/total?sort=sale&page=%d' % (cat, page)
            if cat2:
                url += f'&category={cat2}'
            html = download(url)
            for entry in extract(html):
                art = Artifact(entry[0], entry[1], int(entry[2].replace(',', '')), int(entry[3]), today)
                logger.debug('get %s', art)
                yield art


def download(url: str) -> str:
    logger.info('getting %s', url)
    resp = pm.request('GET', url)
    html = resp.data.decode()
    logger.debug(html)
    time.sleep(0.5)
    return html


def extract(html: str) -> Iterable[tuple]:
    '''从html内容中提取打折商品的信息，每个tr只会对应一个商品'''
    trs = tr_pattern.findall(html)
    assert trs  # 假定总有打折的，如果为空说明pattern出了问题
    for tr in trs:
        if matched := artifact_pattern.findall(tr):
            assert len(matched) == 1
            assert len(matched[0]) == 4
            yield matched[0]


def save(data: Iterable[Artifact], dbname='data.csv'):
    with open(dbname, 'w+', encoding='u8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(('ID', 'Name', 'Price', 'Discount', 'Date'))
        writer.writerows(data)


def load(dbname='data.csv') -> Iterable[Artifact]:
    with open(dbname, encoding='u8', newline='') as f:
        f.readline()  # 去掉header
        for x in csv.reader(f):
            yield Artifact(x[0], x[1], int(x[2]), int(x[3]), date.fromisoformat(x[4]))


def merge(old: ArtifactDict, new: Iterable[Artifact]):
    '''以新数据内容更新旧数据。如果ID在老数据中不存在，或者打折力度更高，或者价格相同但间隔时间超过7天，就更新'''
    for item in new:
        if ((iid := item.ID) not in old
            or item.Discount > old[iid].Discount
            or item.Discount == old[iid].Discount and (item.Date - old[iid].Date).days >= 7):
                old[iid] = item
    logger.debug('merged: %s', new)


def ya_api_builder(ids: list[str]):
    '''Yet another api. Chunk in 100.'''
    from itertools import islice
    endpoint = 'https://www.dlsite.com/maniax/product/info/ajax?cdn_cache_min=1&product_id='
    while chunk := tuple(islice(ids, 100)):
        yield endpoint + '%2C'.join(chunk)


def ya_api_builder_2(n=100):
    '''Yet another api. Get game by sales. The data contains free artifacts.'''
    return 'https://www.dlsite.com/maniax/sapi/=/sex_category/+/order/dl_d/work_type_category/game/per_page/%d/format/json/?cdn_cache=1' % n


def make_html(data: Iterable[Artifact]):
    logger.info('making html.')
    with open('data_tmpl.html', encoding='u8') as f:
        html_tmpl = f.read()
    row_tmpl = '<tr><td>{0}</td><td><a target="_blank" href="https://www.dlsite.com/maniax/work/=/product_id/{0}.html">{1}</a></td><td>{2:,}</td><td>{3}%</td><td><time>{4}</time></td></tr>'
    rows = ''.join((row_tmpl.format(*x) for x in data))
    html = html_tmpl.replace('{DATA}', rows)
    html = re.sub(r'\n\s*', ' ', html)
    with open('data.html', 'w+', encoding='u8') as out:
        out.write(html)


def calc_overview(datalist: Iterable[Artifact]) -> Overview:
    prices = list(sorted(entry.Price for entry in datalist))

    cnt = len(prices)
    p25 = prices[cnt // 4]
    p50 = prices[cnt // 2]
    p75 = prices[cnt // 4 * 3]
    avg = sum(prices) // cnt
    return Overview(cnt, p25, p50, p75, avg)


def main():
    if os.getenv('DLWATCHER_DEBUG'):
        logging.basicConfig(format='%(asctime)s - %(levelname)s:%(message)s', level='DEBUG')
    else:
        logging.basicConfig(format='%(asctime)s - %(levelname)s:%(message)s', level='INFO')

    old = {}
    if os.path.isfile('data.csv'):
        old = load()
        old = ArtifactIter2Dict(old)
    else:
        logger.warning('no existing data.csv.')

    new = get_data()
    merge(old, new)

    datalist = list(sorted(old.values(), key=lambda x: x[0]))  # 要使用多次，所以变为list
    save(datalist)
    logger.info(calc_overview(datalist))

    if os.path.isfile('data_tmpl.html'):
        make_html(datalist)
    else:
        logger.warning('no data_tmpl, not make html.')


if __name__ == '__main__':
    main()
