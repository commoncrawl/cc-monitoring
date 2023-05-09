# cc-monitoring

This code monitors the latency of the Common Crawl CDX index server, and
the AWS Open Data bucket. Time series points are stored in an sqlite3
database, suitable for display in Grafana and other dashboard tools.

# Installation

```
git clone ...
pip install .
```

# Running

```
ccm -v initdb
nohup ccm -v collect
```

This code uses sqlite3's WAL (write ahead log) feature. Due to that, the
directory that the database is in must be writeable by the ccm process.

# Deployment and documentation

* Grafana server (to be named later)
* [User-oriented documentation](https://docs.google.com/document/d/1RJ5LnTGSZY159eRzg8NhRnxSIHusyd6xzEhoEa28ju8/edit?usp=sharing)

# Exporting dashboards

* Click the share icon in the upper left
* Export
* turn on Export for sharing externally
* Save to file
