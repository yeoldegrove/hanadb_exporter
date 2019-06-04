"""
SAP HANA database prometheus data exporter

:author: xarbulu
:organization: SUSE Linux GmbH
:contact: xarbulu@suse.de

:since: 2019-05-09
"""

import logging
import itertools

# TODO: In order to avoid dependencies, import custom prometheus client
try:
    from prometheus_client import core
except ImportError:
    # Load custom prometheus client
    raise NotImplementedError('custom prometheus client not implemented')

from hanadb_exporter.exporters.prometheus_metrics import PrometheusMetrics


class MalformedMetric(Exception):
    """
    Metric malformed method
    """


class SapHanaCollector(object):
    """
    SAP HANA database data exporter
    """

    def __init__(self, conector):
        super(SapHanaCollector, self).__init__()
        self._logger = logging.getLogger(__name__)
        self._hdb_connector = conector

    def _execute(self, query, metric_name, metric_data):
        """
        Create metric object

        Args:
            metric (dict): query, info, type structure dictionary
        """
        try:
            query_result = self._hdb_connector.query(query)
            if metric_data['type'] == "gauge":
                query_columns = []
                metric_dict = {metric_name: []}
                for meta in query_result.metadata:
                    query_columns.append(meta[0])
                for record in query_result.records:
                    metric_dict[metric_name].append(list(itertools.izip(query_columns, record)))
                metric_obj = self._manage_gauge(metric_name, metric_data, query_result.records)
            else:
                raise NotImplementedError('{} type not implemented'.format(metric['type']))
            return metric_obj
        except KeyError as err:
            raise MalformedMetric(err)

    def _manage_gauge(self, metric_name, metric, records):
        """
        Manage Gauge type metric
        """
        # Label not set
        metric_obj = core.GaugeMetricFamily(metric_name, metric['description'], None, metric['labels'], metric['unit'])

        metric_obj.add_metric(metric['labels'], str(records[0][-1]))
        for label_item in records:
            self._logger.info('%s' % (label_item[0]))

        return metric_obj

    def collect(self):
        """
        Collect data from database
        """
        metrics = PrometheusMetrics()
        for query, metric in metrics.data.items():
            for metric_name, metric_data in metric.items():
                metric_obj = self._execute(query, metric_name, metric_data)
                yield metric_obj
