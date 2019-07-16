pyops: OpenSearch made pythonically easy
===========================

OpenSearch python client.

Examples:
```python
>>> import pyops
>>> client = pyops.Client(description_xml_url="https://example.org")

# simple search
>>> raw_results = client.search()

# authenticated search
>>> raw_results = client.search(auth=('username', 'password'))

# advanced search
>>> raw_results = client.search(params={"{eop:instrument?}": {"value": "SAR"}})

# results filtering
>>> raw_results = client.search()
>>> entry_fields = client.get_available_fields()
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
```

TODO
----
- APIs (search, ...)
- json search
- documentation

[HOW TO] DEPLOY
---------------
Update `pyops.__version__.py`
```bash
# create packages
python3 setup.py sdist bdist_wheel
# upload on test.pypi
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
# test install
python3 -m pip install --index-url https://test.pypi.org/simple/ pyops
# upload on pypi
twine upload dist/*
```

CHANGELOG
---------

* v0.0.2 (2019-07-16):
  * Added: authentication management
  * Bugfix: removed unused parameters from search (added regex)
  * Tests: added test_authentication (description_xml_url and authentication params not committed)
  * Issue #1: included tests in packaging