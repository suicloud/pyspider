#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-12-08 22:23:10

import time
import logging
logger = logging.getLogger('bench')

from pyspider.scheduler import Scheduler
from pyspider.fetcher.tornado_fetcher import Fetcher
from pyspider.processor import Processor
from pyspider.result import ResultWorker


class BenchMixin(object):
    def _bench_init(self):
        self.done_cnt = 0
        self.start_time = time.time()
        self.last_cnt = 0
        self.last_report = 0

    def _bench_report(self, name, prefix=0, rjust=0):
        self.done_cnt += 1
        now = time.time()
        if now - self.last_report >= 1:
            rps = float(self.done_cnt - self.last_cnt) / (now - self.last_report)
            output = ''
            if prefix:
                output += " "*prefix
            output += ("%s %s pages (at %d pages/min)" % (name, self.done_cnt, rps*60.0)).rjust(rjust)
            logger.info(output)
            self.last_cnt = self.done_cnt
            self.last_report = now


class BenchScheduler(Scheduler, BenchMixin):
    def __init__(self, *args, **kwargs):
        super(BenchScheduler, self).__init__(*args, **kwargs)
        self._bench_init()

    def on_task_status(self, task):
        self._bench_report('Crawled')
        return super(BenchScheduler, self).on_task_status(task)
    

class BenchFetcher(Fetcher, BenchMixin):
    def __init__(self, *args, **kwargs):
        super(BenchFetcher, self).__init__(*args, **kwargs)
        self._bench_init()

    def on_result(self, type, task, result):
        self._bench_report("Fetched", 0, 75)
        return super(BenchFetcher, self).on_result(type, task, result)


class BenchProcessor(Processor, BenchMixin):
    def __init__(self, *args, **kwargs):
        super(BenchProcessor, self).__init__(*args, **kwargs)
        self._bench_init()

    def on_task(self, task, response):
        self._bench_report("Processed", 75)
        return super(BenchProcessor, self).on_task(task, response)


class BenchResultWorker(ResultWorker, BenchMixin):
    def __init__(self, *args, **kwargs):
        super(BenchResultWorker, self).__init__(*args, **kwargs)
        self._bench_init()

    def on_result(self, task, result):
        self._bench_report("Saved", 0, 150)
        super(BenchResultWorker, self).on_result(task, result)


bench_script = '''
from pyspider.libs.base_handler import *

class Handler(BaseHandler):
    def on_start(self):
        self.crawl('http://localhost:5000/bench', params={'total': %(total)d, 'show': %(show)d}, callback=self.index_page)

    def index_page(self, response):
        for each in response.doc('a[href^="http://"]').items():
            self.crawl(each.attr.href, callback=self.index_page)
        return response.url
'''
