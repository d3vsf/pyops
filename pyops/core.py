# -*- coding: utf-8 -*-

"""
PyOps
~~~~~
This module contais the PyOps Client class.
:copyright: (c) 2018 by Sergio Ferraresi
:license: Apache2, see LICENSE for more details
"""

import logging
import requests
import re
import xml.etree.ElementTree as eltree

try:
    from StringIO import StringIO as read_io
except ImportError:
    from io import BytesIO as read_io

logger = logging.getLogger(__name__)


class Client(object):
    '''
    A user-created :class:`Client <Client>` object.

    Used to prepare a :class:`Client <Client>`, which is used to inquiry an OpenSearch endpoint.

    :param description_xml_url: description.xml of the OpenSearch endpoint.
    :param search_endpoint: OpenSearch endpoint, if :param:`description_xml_url` not available.
    :param type: OpenSearch endpoint type: results or collection.

    Usage::

        >>> import pyops
        >>> client = pyops.Client(description_xml_url="https://example.org")
        >>> raw_results = client.search()
    '''

    def __init__(self, description_xml_url=None, search_endpoint=None, type='collection'):
        if search_endpoint is None and description_xml_url is None:
            msg = 'Neither "search_endpoint" nor "description_xml_url" specified'
            logger.error(msg)
            raise ValueError(msg)

        if type not in ['collection', 'results']:
            msg = 'Neither "collection" nor "results" type specified'
            logger.error(msg)

            raise ValueError(msg)

        self.search_endpoint = search_endpoint
        self.description_xml_url = description_xml_url
        self.type = type

        self.search_template_tag = None
        self.search_template_url = None
        self.search_params = {}
        self.search_param_names = {}
        self.search_url = None
        
        self.content_node = None
        self.pagination = {}
        self.raw_entries = []
        self.filtered_entries = []
        self.errors = []

        if self.search_endpoint and not self.description_xml_url:
            self._get_description_xml_url()

        self._get_search_template()

        self._get_search_params()

        logger.debug('OpenSearch:')
        logger.debug('  > Search Endpoint:    %s' % self.search_endpoint)
        logger.debug('  > description.xml:    %s' % self.description_xml_url)
        logger.debug('  > Search Template:    %s' % self.search_template_url)
        logger.debug('  > Search Params:      %s' % self.search_params)
        logger.debug('  > Search Param Names: %s' % self.search_param_names)
        logger.debug('  > Search URL:         %s' % self.search_url)

    def _get_description_xml_url(self):
        """Retrieves the description.xml URL, if required.
        See: http://www.opensearch.org/Specifications/OpenSearch/1.1/Draft_5#Autodiscovery
        """
        try:
            logger.debug('Fetching description.xml URL from endpoint...')

            r = requests.get(self.search_endpoint, headers={'Content-Type': 'application/atom+xml'})
            if 200 != r.status_code:
                msg = 'Endpoint returned: %d - %s' % (r.status_code, r.reason)
                logger.error(msg)
                raise Exception(msg)
            else:
                tree = eltree.parse(read_io(r.content))
                # for node in tree.iter():
                #    print node.tag, node.attrib

                # http://www.opensearch.org/Specifications/OpenSearch/1.1/Draft_5#Autodiscovery
                self.description_xml_url = tree.find("{http://www.w3.org/2005/Atom}link[@rel='search'][@type='application/opensearchdescription+xml']").get('href')
                if self.description_xml_url:
                    logger.debug('  > DONE: "%s"' % self.description_xml_url)
                else:
                    logger.warning('  > ERROR: NOT a valid OpenSearch endpoint')
        except Exception as e:
            logger.exception(e)

    def _get_search_template(self):
        """Retrieves the Search URL Template.
        See: http://www.opensearch.org/Specifications/OpenSearch/1.1/Draft_5#OpenSearch_description_elements
        
        For internal usege.
        """
        try:
            logger.debug('Fetching Search Template from description.xml...')

            r = requests.get(self.description_xml_url, headers={'Content-Type': 'application/atom+xml'})
            if 200 != r.status_code:
                r = requests.get(self.description_xml_url)
            
            if 200 != r.status_code:
                msg = 'Endpoint returned: %d - %s' % (r.status_code, r.reason)
                logger.error(msg)
                raise Exception(msg)
            else:
                tree = eltree.parse(read_io(r.content))
                #for node in tree.iter():
                #    print node.tag, node.attrib

                # http://www.opensearch.org/Specifications/OpenSearch/1.1/Draft_5#OpenSearch_description_elements
                try:
                    self.search_template_tag = tree.find('{http://a9.com/-/spec/opensearch/1.1/}Url[@rel="%s"][@type="application/atom+xml"]' % self.type)
                except Exception:  # particular case
                    self.search_template_tag = tree.find('{http://a9.com/-/spec/opensearch/1.1/}Url[@type="application/atom+xml"]')
                # particular case
                if self.search_template_tag is None or not len(self.search_template_tag):
                    self.search_template_tag = tree.find('{http://a9.com/-/spec/opensearch/1.1/}Url[@type="application/atom+xml"]')
                # particular case
                if self.search_template_tag is None or not len(self.search_template_tag):
                    self.search_template_tag = tree.find('{http://a9.com/-/spec/opensearch/1.1/}Url[@type="application/rss+xml"]')
                # particular case
                if self.search_template_tag is None or not len(self.search_template_tag):
                    self.search_template_tag = tree.find('{http://a9.com/-/spec/opensearch/1.1/}Url[@type="text/html"]')

                self.search_template_url = self.search_template_tag.get('template')
                self.search_url = self.search_template_url
                
                if self.search_template_url:
                    logger.debug('  > DONE')
                else:
                    msg = 'NOT a valid OpenSearch template'
                    logger.error('  > ERROR: %s' % msg)
                    raise Exception(msg)
        except Exception as e:
            logger.exception(e)

    def _get_search_params(self):
        """Retrieves Search URL Template params.
        See: http://www.opensearch.org/Specifications/OpenSearch/1.1/Draft_5#OpenSearch_URL_template_syntax
        
        For internal usege.
        """

        try:
            logger.debug('Fetching Search Params...')

            tags = re.findall('\{[\w\:\?]+\}', self.search_template_url)

            self.search_params = {}
            self.search_param_names = {}
            for t in tags:
                clean_tag = t.replace('{', '').replace('?', '').replace('}', '')
                key = clean_tag.replace(':', '_')
                self.search_params[key] = {}
                self.search_params[key]['clean_tag'] = clean_tag
                self.search_params[key]['full_tag'] = t

                for node in self.search_template_tag:
                    if clean_tag in node.attrib['value']:
                        self.search_param_names[node.attrib['name']] = key

                        if 'time' in node.attrib['value']:
                            self.search_params[key]['type'] = 'date'
                        else:
                            self.search_params[key]['type'] = 'text'

                        if 'title' in node.attrib:
                            self.search_params[key]['title'] = node.attrib['title']
                        if 'pattern' in node.attrib:
                            self.search_params[key]['pattern'] = node.attrib['pattern']
                        if 'minimum' in node.attrib:
                            self.search_params[key]['minimum'] = node.attrib['minimum']
                        if 'minInclusive' in node.attrib:
                            self.search_params[key]['minInclusive'] = node.attrib['minInclusive']
                        if 'maxInclusive' in node.attrib:
                            self.search_params[key]['maxInclusive'] = node.attrib['maxInclusive']

                        optChildren = node.findall("{http://a9.com/-/spec/opensearch/extensions/parameters/1.0/}Option")
                        if len(optChildren) > 0:
                            self.search_params[key]['type'] = 'select'
                            self.search_params[key]['options'] = {}
                            for oc in optChildren:
                                oc_tmp = oc.attrib['value']
                                if 'label' in oc.attrib:
                                    oc_tmp = oc.attrib['label']
                                self.search_params[key]['options'][oc_tmp] = oc.attrib['value']
                        break
                else:
                    self.search_param_names[key] = key
                    if 'time' in key:
                        self.search_params[key]['type'] = 'date'
                    else:
                        self.search_params[key]['type'] = 'text'
            logger.debug('  > DONE')
        except Exception as e:
            logger.exception(e)

    def _get_href_params(self, tree, regex):
        """For internal usege."""
        node = tree.find(regex)
        out = {}
        if node is not None:
            href = node.get('href')
            index = href.find('&')
            if index > 0:
                out = {x.split('=')[0]: x.split('=')[1] for x in href[index + 1:].split('&')}

        return out

    def _node_list_to_json(self, node_list):
        """Converts a node list to a json. Data is not interpreted.
        
        For internal usege.
        """
        if len(list(node_list)) == 1:
            node_out = []
            for n in node_list[0].iter():
                if 'entry' not in n.tag:
                    node_out.append({
                        'tag': n.tag,
                        'name': n.tag.split('}')[1] if '}' in n.tag else n.tag,
                        'attrs': n.attrib,
                        'text': n.text,
                        'children': self._node_list_to_json(n) if len(list(n)) else []
                    })
            return node_out
        else:
            node_list_out = []
            for n in node_list:
                node_out = []
                for nn in n.iter():
                    if 'entry' not in nn.tag:
                        node_out.append({
                            'tag': nn.tag,
                            'name': nn.tag.split('}')[1] if '}' in nn.tag else nn.tag,
                            'attrs': nn.attrib,
                            'text': nn.text,
                            'children': self._node_list_to_json(nn) if len(list(nn)) else []
                        })
                node_list_out.append(node_out)
            return node_list_out

    def search(self, force_HTTPS=True, params={}, auth=()):
        """Does an OpenSearch call to the Search URL Template replacing the Search URL Template params with the given ones.

        :param force_HTTPS: forces the connection to be HTTPS.
        :param params: the input parameters for the Search query.

        Usage::

            >>> # Without Params
            >>> raw_results = client.search()

        or::

            >>> With Params
            >>> param_names = client.search_param_names
            >>> input_params = {}
            >>> if 'searchTerms' in param_names:
            >>>   input_params[params["searchTerms"]["full_tag"]] = {"value": "sentinel1"}
            >>> #   Pagination Params
            >>> if custom_start_params:
            >>>     for csp in custom_start_params:
            >>>         value = custom_start_params[csp]
            >>>         if value and csp in param_names:
            >>>             input_params[params[csp]["full_tag"]] = {"value": value}
            >>> #   Other Params
            >>> for ff in form_fields:
            >>>     value = form_fields[ff]
            >>>     if value and ff in param_names:
            >>>         input_params[params[ff]["full_tag"]] = {"value": value}
            >>> # Get Raw Results
            >>> raw_results = client.search(params=input_params)
        """
        try:
            logger.debug('Searching...')

            if force_HTTPS and self.search_url.startswith('http://'):
                self.search_url = self.search_url.replace('http://', 'https://')

            # replace params
            for sp_indx in self.search_params:
                sp_tag = self.search_params[sp_indx]['full_tag']
                value = params[sp_tag]['value'] if sp_tag in params else None
                if value:
                    self.search_url = self.search_url.replace(sp_tag, value)
                else:
                    self.search_url = re.sub(r'&\w+=' + sp_tag.replace('?', '\?'), '', self.search_url)
                    self.search_url = re.sub(r'\?\w+=' + sp_tag.replace('?', '\?'), '', self.search_url)
            logger.debug('  > Search URL: %s' % self.search_url)

            # if ? not present
            and_indx = self.search_url.find('&')
            qm_indx = self.search_url.find('?')
            if (-1 == qm_indx) or (qm_indx > and_indx):
                self.search_url = self.search_url.replace('&', '?', 1)

            # remove unset parameters
            self.search_url = re.sub('[\?&/]\w*=*\{\w+:*\w+\?*\}*', '', self.search_url)
            self.search_url = re.sub(
                '((\s?AND\s)\w*:*\{\w+:*\w+\??\}*)|((\s?AND\s)\w+:\[\{\w+:\w+\??\}\sTO\s\{\w+:\w+\??\}\])|((\s?AND\s)?\w+:(%22|")\w+\(\{\w+:*\w+\??\}*\)(%22|"))', '', self.search_url)
            print(self.search_url)

            if auth and isinstance(auth, tuple) and 2 == len(auth):
                print(self.search_url)
                print(auth)
                r = requests.get(self.search_url, auth=auth)
            else:
                r = requests.get(self.search_url)
            self.content_node = eltree.fromstring(r.content)
            if 200 != r.status_code:
                msg = 'Endpoint returned: %d - %s' % (r.status_code, r.reason)
                self.errors.append(msg)
                logger.error(msg)

                try:
                    exception = self.content_node.find('{http://www.opengis.net/ows/2.0}Exception')
                    if exception:
                        ex_code = exception.attrib['exceptionCode']
                        ex_loca = exception.attrib['locator']
                        ex_text = exception.find('{http://www.opengis.net/ows/2.0}ExceptionText').text.lstrip().rstrip()

                        msg = 'Exception code: "%s"\n\tLocator: "%s"\n\tDescription: "%s"' % (ex_code, ex_loca, ex_text)
                        self.errors.append(msg)
                        logger.error(msg)
        
                    exception = self.content_node.find('{http://www.w3.org/2003/05/soap-envelope}Text')
                    if exception:
                        ex_text = exception.text.lstrip().rstrip()

                        self.errors.append(msg)
                        logger.error(msg)
                except Exception as e:
                    pass  # TODO
            else:
                # for node in self.content_node.iter():
                #     logger.debug('%s %s %s' % (node.tag, node.attrib, node.text))

                # pagination
                # total number of results
                total_results_tag = self.content_node.find('{http://a9.com/-/spec/opensearch/1.1/}totalResults')
                self.pagination['total_results'] = int(total_results_tag.text) if total_results_tag is not None else 0
                # start index
                start_index_tag = self.content_node.find('{http: // a9.com/-/spec/opensearch/1.1/}startIndex')
                self.pagination['start_index'] = int(start_index_tag.text) if start_index_tag is not None else 0
                # items per page
                items_per_page_tag = self.content_node.find('{http://a9.com/-/spec/opensearch/1.1/}itemsPerPage')
                self.pagination['items_per_page'] = int(items_per_page_tag.text) if items_per_page_tag is not None else 0
                # first page
                self.pagination['first'] = self._get_href_params(self.content_node, '{http://www.w3.org/2005/Atom}link[@rel="first"]')
                if not self.pagination['first'] and self.pagination['total_results'] > 0:
                    self.pagination['first']['startIndex'] = 1
                # prev page
                self.pagination['prev'] = self._get_href_params(self.content_node, '{http://www.w3.org/2005/Atom}link[@rel="previous"]')
                if not self.pagination['prev'] and self.pagination['total_results'] > 0:
                    prev_page_index = self.pagination['start_index'] - self.pagination['items_per_page']
                    self.pagination['prev']['startIndex'] = 1 if prev_page_index <= 0 else prev_page_index
                # next page
                self.pagination['next'] = self._get_href_params(self.content_node, '{http://www.w3.org/2005/Atom}link[@rel="next"]')
                if not self.pagination['next'] and self.pagination['total_results'] > 0:
                    next_page_index = self.pagination['start_index'] + self.pagination['items_per_page']
                    last_page_index = self.pagination['total_results'] - self.pagination['items_per_page']
                    self.pagination['next']['startIndex'] = last_page_index if next_page_index >= self.pagination['total_results'] else next_page_index
                # last page
                self.pagination['last'] = self._get_href_params(self.content_node, '{http://www.w3.org/2005/Atom}link[@rel="last"]')
                if not self.pagination['last'] and self.pagination['total_results'] > 0:
                    tmp_mod = self.pagination['total_results'] % self.pagination['items_per_page']  # Get mod of: number of elements / items per page
                    self.pagination['last']['startIndex'] = (self.pagination['total_results'] - self.pagination['items_per_page'] + 1) if tmp_mod == 0 else (self.pagination['total_results'] - tmp_mod + 1)
                # query params
                self.pagination['query_params'] = self._get_href_params(self.content_node, '{http://www.w3.org/2005/Atom}link[@rel="self"]')
                # description.xml URL
                description_xml_url_tag = self.content_node.find('{http://www.w3.org/2005/Atom}link[@rel="search"]')
                description_xml_url = description_xml_url_tag.get('href') if description_xml_url_tag is not None else None
                if not description_xml_url:
                    description_xml_url = self.description_xml_url

                # results
                entry_list = self.content_node.findall('{http://www.w3.org/2005/Atom}entry')
                if not entry_list and (self.pagination['total_results'] > 0):  # particular case
                    entry_list = self.content_node.find('channel').findall('item')
                self.raw_entries = self._node_list_to_json(entry_list)


                # georss_entry = GeoRssDecoder(parent_node=r, polygons_over_boxes=terradue)
                # entry['GeomList'] = georss_entry.polygon_list
                # for tmp in entry['GeomList']:
                #     if tmp['raw']:
                #         env = ogr.CreateGeometryFromWkt(tmp['raw']).GetEnvelope()
                #         tmp['bbox'] = [env[2], env[0], env[3], env[1]]
                #     if modis and form_fields['rep'] in ['MOD05_L2_2']:
                #         tmp['mode'] = 'lonlat'

                # if r.find('{http://www.w3.org/2005/Atom}summary') is not None and r.find('{http://www.w3.org/2005/Atom}summary').text is not None:
                #     _decode_summary(html.fromstring(r.find('{http://www.w3.org/2005/Atom}summary').text), entry)

        except Exception as e:
            logger.exception(e)
        return self.raw_entries

    def get_available_fields(self):
        """Returns the list of fields available for each entry.

        Usage::

            >>> raw_results = client.search()
            >>> entry_fields = client.get_available_fields()
        """
        self.fields = []
        if len(self.raw_entries) > 0:
            for f in self.raw_entries[0]:
                tmp = {
                    'tag': f['tag'],
                    'name': f['name'],
                }
                if len(f['attrs']) > 0 and 'rel' in f['attrs']:
                    tmp['rel'] = f['attrs']['rel']
                self.fields.append(tmp)

        return self.fields

    def filter_entries(self, fields=[]):
        """Returns for each entry only the required fields.

        :param fields: list of required fields.

        Usage::

            >>>  filtered_results = client.filter_entries([{
            >>>     "tag": "{http://www.w3.org/2005/Atom}id",
            >>>     "name": "id"
            >>> }, {
            >>>     "tag": "{http://www.w3.org/2005/Atom}title",
            >>>     "name": "title"
            >>> }, {
            >>>     "tag": "{http://www.w3.org/2005/Atom}summary",
            >>>     "name": "summary"
            >>> }, {
            >>>     "tag": "{http://www.w3.org/2005/Atom}published",
            >>>     "name": "published"
            >>> }, {
            >>>     "tag": "{http://www.w3.org/2005/Atom}updated",
            >>>     "name": "updated"
            >>> }, {
            >>>     "tag": "{http://www.w3.org/2005/Atom}link",
            >>>     "name": "link",
            >>>     "rel": "enclosure"
            >>> }])
        """
        for r in self.raw_entries:
            tmp = []
            for rf in r:
                for f in fields:
                    if rf['tag'] == f['tag'] and rf['name'] == f['name'] and (('rel' not in f) or ('rel' in f and rf['attrs']['rel'] == f['rel'])):
                        tmp.append(rf)
            self.filtered_entries.append(tmp)
        return self.filtered_entries
