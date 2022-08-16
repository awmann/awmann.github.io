================================================================================
Title: Spectro-Thermometry of M dwarfs and their candidate planets: 
       too hot, too cool, or just right? 
Authors: Mann A.W., Gaidos E., Ansdell M.
================================================================================
Description of contents: This package file includes .fits files of three 
	different sets of spectra: the habitable zone candidates, the KOIs 
	(excluding the habitable zone candidates), and the calibrators. 
	The calibrators are absolutely flux calibrated, and contain both SNIFS
	and SpeX data, as well as BT-SETTL models to fill int he gaps. The 
	habitable zone candidates are similar, but are not absolutely flux 
	calibrated. Data based on BT-SETTL models have errors set to 0.
	The KOIs contain only SNIFS data (optical). See Sections 3 and 4 for 
	more information. 
	Names for the KOIs are their KOI number. Calibrator stars are given their 
	GJ designation.
	Calibrator spectra go from 0.2 to 3.0 microns, this does not include 
	our extrapolation beyond these regions (see Section 4.1 for more details).

System requirements: Requires a fits file reader. Fits files were created using 
  the IDL Function MWRFITS.  

Additional comments: In the header of each .fits file you will find:
	- The star's KOI or GJ name (NAME)                                         
	- The star's KIC ID (KID), not available for calibrators                                                 
	- The instrument(s) used (INSTRUM)
	- The telescope(s) used (TELESCO)
	- Notes and warnings (NOTES)                                        
   The three columns of the array are: 
	- COLUMN1 =         Wavelength [microns]                                          
	- COLUMN2 =         Flux  [erg s-1 cm-2 A-1]                                          
	- COLUMN3 =         Error [erg s-1 cm-2 A-1]              

================================================================================

