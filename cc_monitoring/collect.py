import time
import secrets
import random
import sys
from collections import defaultdict
from functools import partial

import requests


headers = {'User-Agent': 'time-cc.py greg at common crawl'}


def static_file(url=None):
    # success: a json respose that parses and has a size
    resp = requests.get('https://index.commoncrawl.org/collinfo.json', timeout=30, headers=headers)
    resp.raise_for_status()
    assert len(resp.text) > 1000, 'static file long enough'
    j = resp.json()  # does it parse


def first_level(url=None, expect_404=False):
    # success: an integer
    resp = requests.get('https://index.commoncrawl.org/CC-MAIN-2023-14-index',
                        params={'url': url, 'showNumPages': 'true', 'limit': 1},
                        timeout=30, headers=headers)
    if resp.status_code == 404:
        if expect_404:
            return
        else:
            raise ValueError('expected a 404, got '+str(resp.status_code))
    resp.raise_for_status()

    # {"pages": 1, "pageSize": 5, "blocks": 1}
    j = resp.json()
    assert len(j) == 3, 'first_level json object has 3 fields'


def second_level(url=None, expect_404=False):
    # success: one line
    resp = requests.get('https://index.commoncrawl.org/CC-MAIN-2023-14-index',
                        params={'limit': 1, 'url': url, 'output': 'json', 'page': 0},
                        timeout=30, headers=headers)
    if resp.status_code == 404:
        if expect_404:
            return
        else:
            raise ValueError('expected a 404, got '+str(resp.status_code))
    resp.raise_for_status()

    # {"urlkey": "com,pbm)/", "timestamp": "20230401021713", "url": "https://www.pbm.com/", "mime": "text/html", "mime-detected": "text/html", "status": "200", "digest": "JJ3ZSV7NTSBFMGG6GEK7QZI3ELJIBHTN", "length": "1766", "offset": "1019004815", "filename": "crawl-data/CC-MAIN-2023-14/segments/1679296949694.55/warc/CC-MAIN-20230401001704-20230401031704-00168.warc.gz", "languages": "eng", "encoding": "UTF-8"}
    j = resp.json()
    assert len(j) >= 12, 'second_level json object has >=12 fields'


cfront = 'https://data.commoncrawl.org/'
fname = 'crawl-data/CC-MAIN-2023-14/segments/1679296949694.55/warc/CC-MAIN-20230401001704-20230401031704-00168.warc.gz'
flength = 1202988820  # bytes


def s3_hit(url=None):
    offset = 0
    length = 4096
    headers2 = headers.copy()
    headers2['Range'] = 'bytes={}-{}'.format(offset, offset+length-1)
    resp = requests.get(cfront + fname, timeout=30, headers=headers2)
    resp.raise_for_status()
    assert len(resp.content) == 4096, 's3 hit returns 4096 bytes'


def s3_miss(url=None):
    blocks = flength / 4096
    offset = random.randrange(int(blocks)) * 4096
    length = 4096
    headers2 = headers.copy()
    headers2['Range'] = 'bytes={}-{}'.format(offset, offset+length-1)
    resp = requests.get(cfront + fname, timeout=30, headers=headers2)
    resp.raise_for_status()
    assert len(resp.content) == 4096, 's3 miss returns 4096 bytes'


def munge(value):
    if value is None:
        return None
    return round(value, 3)


def wrap(func, errors, url='pbm.com'):
    t0 = time.time()
    try:
        resp = func(url=url)
    except Exception as e:
        if isinstance(e, requests.Timeout):
            kind = 'timeout'
        elif isinstance(e, requests.ConnectionError):
            kind = 'connection_error'
        elif isinstance(e, requests.HTTPError):
            if e.resp.status_code in {500, 503}:
                kind = 'slow_down'
            else:
                kind = 'http_'+str(e.resp.status_code)
        else:
            print('Saw surprising exception: '+repr(e), file=sys.stderr)
            kind = 'unknown'
        errors[kind] += 1
        return None
    return time.time() - t0


def collect_one(verbose=0):
    random_url = secrets.token_urlsafe(nbytes=16) + '.com'
    cdx_stuff = [
        ('t_static', static_file),
        ('t_first', first_level),
        ('t_second', second_level),
        ('t_first_miss', partial(first_level, url=random_url, expect_404=True)),
        ('t_second_miss', partial(second_level, url=random_url, expect_404=True)),
    ]
    s3_stuff = [
        ('t_s3', s3_hit),
        ('t_s3_miss', s3_miss),
    ]

    data = {}
    cdx_errors = defaultdict(int)
    for name, func in cdx_stuff:
        data[name] = munge(wrap(func, cdx_errors))
        if verbose:
            print(name, data[name])
    s3_errors = defaultdict(int)
    for name, func in s3_stuff:
        data[name] = munge(wrap(func, s3_errors))

    errors = {}
    for k, v in cdx_errors.items():
        errors['cdx_'+k] = v
    for k, v in s3_errors.items():
        errors['s3_'+k] = v

    if verbose:
        print('errors', errors)

    return data, errors
