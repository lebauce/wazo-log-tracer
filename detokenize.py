#!/usr/bin/env python

import re
import sys

# 6bb7ff00-88e9-4677-ba38-13e0155eb0f5
token_re = re.compile(r'\w{8}-\w{4}-\w{4}-\w{4}-\w{12}')

for line in sys.stdin:
    line = token_re.sub("XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX", line)
    sys.stdout.write(line)
