#!/bin/bash

## Processing
## TODO: Does this really take the temperature?
cat $IN |
    cut -c 89-92 |
    grep -v 999 |
    sort -rn |
    head -n1
