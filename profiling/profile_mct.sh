#!/usr/bin/bash
python -m cProfile -s tottime example_script.py $1 $2 > profiling_$1.txt