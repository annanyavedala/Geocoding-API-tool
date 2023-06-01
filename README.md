# Geocoding-API-tool
 This command line tool helps to geocode addresses using the ArcGIS API as well as the Google API. It also geocodes PO Box addresses. 
 Additionally, it returns the cost of geocoding before the geocoding begins.
 This repository can be used as a command line tool as well as an API.
 
HOW TO RUN THIS FILE:

a) Obtain the ArcGIS API key from -  https://developers.arcgis.com/

b) Install ArcGIS using pip install arcgis

c) On the command line, run the command:

python SDOHMappingTool.py --input 'input_file_path' --output 'output_file_path'

d) Run the test.py in order to use it as a local API.

REQUIREMENTS TO RUN THIS TOOL SUCCESSFULLY:

a) The input file must have the following columns: 

  -'Street'- First line of the address
  
  -'City'- City of residence
  
  -'State'- State of residence
