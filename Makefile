install:
	pip install .[dev]

initdb:
	ccm -v initdb
