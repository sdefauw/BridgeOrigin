#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function

from elasticsearch import Elasticsearch

import brorig.log as log


class SearchManager:

    def __init__(self, index):
        self.index = "brorig_%s" % index.lower()
        self.es = Elasticsearch()
        if not self.es.ping():
            log.warning("Search engine not available")
            self.es = None
            return
        self.es.indices.create(index=self.index)

    def packet_population(self, network):
        """
        Transfer all search criterion packet to the search engine.
        """
        if not self.es:
            return
        log.debug("Adding packet in search engine...")
        packets = [p for n in network.nodes for p in n.packet_list()] + \
                  [p for l in network.links for p in l.packet_list()]
        for p in packets:
            self.es.index(index=self.index, doc_type='packets', id=p.uuid, body=p.search_criterion())
        log.debug("All packets added to the search engine")

    def clean(self):
        """
        Clean the search engine
        """
        if not self.es:
            return
        log.debug("Destroy index %s in search engine" % self.index)
        self.es.indices.delete(index=self.index, ignore=[400, 404])

    def search(self, filter):
        """
        Ask to the search engine to gives the most pertinent result based on the user filter
        :param filter: request user filter
        :return: list of packet UUID resulted of the search request
        """
        serialized_filter = filter.copy()
        # TODO support time ?
        del serialized_filter['time']
        if serialized_filter == {}:
            return None
        macthes = {"match": {c: v} for (c, v) in serialized_filter.iteritems()}
        result = self.es.search(index=self.index, doc_type='packets', body={
            "query": {
                "bool": {
                    "must": macthes
                }
            }
        })
        log.debug("Search engine found %s packets" % result['hits']['total'])
        return [h['_id'] for h in result['hits']['hits']]

    def __del__(self):
        self.clean()
