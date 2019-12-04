# Tools to help analyzing Wazo service logs

## extractor.py

This tool re arrage Wazo service logs in order to extract
backtraces and provide a single file for request/response that
can be analyze with goaccess.

```
python extractor.py wazo-auth.log*
```

This command generated 3 files:

* wazo-auth-nobt.log: log file with all the backtraces removed
* wazo-auth-bt.log: log file with only the backtraces
* wazo-auth-req.log: log file with request and response merged, can be analyzed with goaccess

## detokenize.py

Replace tokens from the log by a unique placeholder. This can be applied before goaccess
analysis.

```
cat wazo-auth-req.log | python detokenize.py > detokenized.log
```

## mkgoaccess

This short shell script call goaccess with the required format to read *-req.log" files

```
mkgoaccess wazo-auth-req.log
```

or 

```
mkgoaccess detokenized.log
```
