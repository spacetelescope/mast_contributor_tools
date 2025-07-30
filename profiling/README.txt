Basic time profiling for mast_contributor_tools filename checker.

`profile_mct.sh` is an executable script that will run the filename checker on 
a user-specified HLSP. Intended use is to run the script on one of the 
archwork machines, so that the HLSP test directory is available.

Usage examples:
>>> ./profile_mct.sh relics
>>> ./profile_mct.sh t16 /ifs/archive/ops/mast/public/hlsp/t16/s0003/cam1-ccd1

Profiler output is saved to profiling_<hlsp_name>.txt.