Keyword finder README
=====================
This is a small atomic function to quickly check the metadata for HLSPS it works by scouring the header and extensions of a fits file for HLSP keywords and rules defined in the metadata_keywords.json file.

at present it only works for FITS files and is best suited to grabbing metadata for HLSP images. It can run for spectral-images, and spectral-bin but that has not been worked on too heavily.

To run you need to ensure the following packages are install
1. json
2. pandas

Checking a single .fits file (image)
====================================
All that is needed is 
1. fits_file: The path to the fits file you would like to test
2. meta_types (str): the type of hlsp metadata you would like to check against, this can been
    * image
    * spectral-image
    * spectral-bin
3. verbose (bool): Prints the summary section of the hlsp metadata search that should look something like the example below

Example:
===========
Running >

fits_file = "/Users/areedy/Software/scratch/hlsp_pie_hst_wfc3_all-galaxies_multi_v1_phot-cat.fits"
keyword_finder(fits_file=fits_file,
                meta_types='image',
                verbose=True)

Returns >

     KEYWORD CATAGORY         RULE    FOUND EXT EXPECT EXT FOUND                           VALUE CONDITION_KEYWORD CONDITION_VALUE
0   DATE-BEG   common     required     FAIL         []        []                              []           MJD-BEG                
1   DATE-END   common     required     FAIL         []        []                              []           MJD-END                
2        DOI   common     required  SUCCESS        [0]       [0]            [10.17909/emsa-yj13]                                  
3    EQUINOX   common     required  SUCCESS         []       [1]                          [2000]           RADESYS            ICRS
4     HLSPID   common     required  SUCCESS        [0]       [0]                           [PIE]                                  
5   HLSPLEAD   common  recommended  SUCCESS        [0]       [0]              [Claudia Scarlata]                                  
6   HLSPNAME   common  recommended  SUCCESS        [0]       [0]  [Parallel Ionizing Emissivity]                                  
7   HLSPTARG   common     required  SUCCESS        [0]       [0]                [PIE-ALL-FIELDS]                                  
8    HLSPVER   common     required  SUCCESS        [0]       [0]                            [v1]                                  
9   INSTRUME   common     required  SUCCESS        [0]       [0]                          [WFC3]                                  
10   LICENSE   common     required     FAIL        [0]        []                              []                                  
11  LICENURL   common     required     FAIL        [0]        []                              []                                  
12   MJD-BEG   common     required  SUCCESS         []       [0]                [59920.67232639]          DATE-BEG                
13   MJD-END   common     required  SUCCESS         []       [0]                [60741.40424769]          DATE-END                
14   MJD-MID   common     required  SUCCESS         []       [0]                [60331.03828704]          DATE-AVG                
15  OBSERVAT   common     required  SUCCESS        [0]       [0]                           [HST]                                  
16  PROPOSID   common    suggested  SUCCESS        [0]       [0]                  [17147, 17518]                                  
17  REFERENC   common    suggested     FAIL        [0]        []                              []                                  
18   TELAPSE   common  recommended     FAIL         []        []                              []                                  
19  TELESCOP   common     required  SUCCESS        [0]       [0]                           [HST]                                  
20   TIMESYS   common     required  SUCCESS         []       [0]                           [UTC]                                  
21   XPOSURE   common     required     FAIL         []        []                              []                                  
22  APERTURE    image    suggested     FAIL         []        []                              []                                  
23     BUNIT    image     required     FAIL         []        []                              []                                  
24     CDi_j    image     required     FAIL         []        []                              []             PCi_j                
25    CDELTi    image     required     FAIL         []        []                              []             CDi_j                
26    CRPIXj    image     required     FAIL         []        []                              []                                  
27    CRVALi    image     required     FAIL         []        []                              []                                  
28    CTYPEi    image     required     FAIL         []        []                              []                                  
29    CUNITi    image    suggested     FAIL         []        []                              []                                  
30  DETECTOR    image    suggested     FAIL         []        []                              []                                  
31    FILTER    image     required     FAIL         []        []                              []                                  
32     PCi_j    image     required     FAIL         []        []                              []             CDi_j                
33   RADESYS    image     required     FAIL         []        []                              []                                  
34  DEC_TARG    image     required     FAIL         []        []                              []                                  
35   RA_TARG    image     required     FAIL         []        []                              []                                  
36   PSFSIZE    image  recommended     FAIL         []        []                              []                                  
37   WCSAXES    image  recommended     FAIL         []        []                              []                                  

SUMMARY
      CATEGORY  FOUND  TOTAL  PERCENT                                            MISSING
0     required     12     28     42.9  [DATE-BEG, DATE-END, LICENSE, LICENURL, XPOSUR...]
1  recommended      2      5     40.0                        [TELAPSE, PSFSIZE, WCSAXES]
2    suggested      1      5     20.0             [REFERENC, APERTURE, CUNITi, DETECTOR]

NOTES AND FUTURE WORK
======================
* The big thing, and what I was trying to remember yesterday, is the rules aren't factored into the final "grade". 
  For example you can see from this generated report for PIES that it only found 24 of the 28 required keywords but this is incorrect as CD and MJD are used.

  This means that the operator still nees to investigate the 

* While it does display the rules for a given keyword. It does not at present delinitate that a value _connot_ be present e.x. RADESYS being ICRS but it's not really clear that EQUINOX cannot be 
  present if that RADESYS is ICRS, so that needs to be worked on a bit.