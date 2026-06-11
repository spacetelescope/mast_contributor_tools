------------------
keyword_finder.py
------------------

This script is a small atomic function to search for keywords within a FITS file. All that is needed to run it is a path to a .fits file and a keyword to search for. It will then
run through all available headers within the fits file and search for that keyword and return both exact matches, and prefix matches (Useful for keywords like CDELT or if RA has 
something appending to it).

It is currently set up to be run from the command line

    $ python keyword_finder.py /<path>/<to>/<fits>/hlsp_lacos_hst_acs_j011309+000223_f150lp_v1.0_img.fits -k RA
    
    which in this example would return
    
        > [FOUND] Ext 0 (PRIMARY)
            PREFIX  RADESYS = ICRS
            PREFIX  RA_TARG = 18.287133794
        > [NOT FOUND] Ext 1 (F150LP-IMG)
        > [NOT FOUND] Ext 2 (F150LP-STD)

Moving forward the vision would be to exapand this function to take in the metadata lists from our internal metadata keyword lists and have all the checking be automatic. 

