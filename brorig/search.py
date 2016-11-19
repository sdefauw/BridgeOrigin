#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function

from elasticsearch import Elasticsearch

import brorig.log as log


class SearchManager:

    def __init__(self, network):
        self.net = network
        self.es = Elasticsearch()

    def populate_search_engine(self):
        """
        Transfer all search criterion packet to the search engine.
        """
        log.debug("Adding packet in search engine...")
        packets = [p for n in self.net.nodes for p in n.packet_list()] + \
                  [p for l in self.net.links for p in l.packet_list()]
        for p in packets:
            self.es.index(index="brorig", doc_type='packets', id=p.uuid, body=p.search_criterion())
        log.debug("All packets added to the search engine")

    def clean(self):
        """
        Clean the search engine
        """
        self.es.delete(inde="brorig", ignore=[400, 404])
