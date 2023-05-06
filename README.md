# cc-monitoring

This code monitors the latency of the Common Crawl CDX index server, and
the AWS Open Data bucket.

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
