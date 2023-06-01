#HOW TO RUN THIS FILE
#Obtain the ArcGIS API key from https://developers.arcgis.com/
#Install ArcGIS using pip install arcgis
#On the command line, run the command: python SDOHMappingTool.py --input 'input_file_path' --output 'output_file_path'
#Requirements to run this file include: 
#The input file must have the following columns: 
#'Street'- First line of the address
#'City'- City of residence
#'State'- State of residence

from arcgis.gis import GIS
from arcgis.geocoding import get_geocoders, batch_geocode,geocode
import pandas as pd
from arcgis.geocoding import Geocoder, get_geocoders
from os.path import exists
import json
import requests
import argparse

#Function to use arcGIS to map addresses to latitude and longitudes.

def get_cost_arcGIS(df):
    # In ArcGIS, we have 20,000 free requests(without storing) and then $0.5 for every 1000 requests after that.
    cost=20000
    if(len(df)<=cost):
        # print('No cost will be applied for your request')
        return 0
    else:
        val=(len(df)-20000)*0.5
        # print('The cost for your conversion will be $' + str(val))
        return val
        

def get_multiline_result(df, IDR_DS):
    # gis= GIS(api_key='Insert your key here')
    my_geocoder1 = get_geocoders(gis)[0]
    geocoder_url = 'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer'
  #Initialize the encoder to convert address to 9-digit zip.
    esrinl_geocoder = Geocoder(geocoder_url, gis)
    zip5list=[]
    zip9list=[]
    states=[]
    coordinate_x=[]
    coordinate_y=[]
    score=[]
    MLA= IDR_DS.copy()
  #Copying all the required columns into the final dataset.
    df['Street']=IDR_DS['Street']
    df['City']=IDR_DS['City']
    df['State']=IDR_DS['State']
  #Converting the given dataset into the format that is acceptable by the ARCGIS API.
    MLA.rename(columns={"Street": "Address", "State":"Region", "Zip 9":"Postal"}, inplace=True)
  #Converting the dataframe into a dictionary to pass into the geocoder.
    MLA = MLA.to_dict('index')
    for idx in range(len(MLA)):
        results = geocode(MLA[idx],  geocoder=esrinl_geocoder)
        if results is None:
            zip9list.append('None')
            zip5list.append('None')
        #5-digit zip
        str1=str(results[0]['attributes']['Postal'])
        zip5list.append(str1)
        #+4 extension
        str2=str(results[0]['attributes']['PostalExt'])
        str1+=str2
        #Append the 5 digit zip with the +4 extension.
        zip9list.append(str1)
        #Append the score
        score.append(results[0]['score'])
        #Append the state abbreviation in order to directly retrieve the zip codes from the required files.
        states.append(results[0]['attributes']['RegionAbbr'])
        #Append all the x coordinate values
        coordinate_x.append(results[0]['location']['x'])
        #Append all the y coordinate values
        coordinate_y.append(results[0]['location']['y'])
    df['zip-9-generated']=zip9list
    df['zip-5']=zip5list
    df['coordinate_x']=coordinate_x
    df['coordinate_y']=coordinate_y
    df['score']=score
    
    return df

#Function to fill PO Box address 9 digit zips separately.
def fill_PO_Box_addresses(final_df):
    print('Hi')
    df2= final_df
    zip9=[]
  #The PO Box address provides the +4 in the 9-digit zip. We extract this from the address itself.
    for idx,row in final_df.iterrows():
        if 'po box' in (row['Street']).lower():
            x=list(row['Street'].split())
            if(len(x[-1])==4):
                zip9.append(row['zip-5']+x[-1])
            elif(len(x[-1])>4):
                zip9.append(row['zip-5']+x[-1][-4:])
            else:
                x[-1]=x[-1].zfill(4)
                zip9.append(row['zip-5']+x[-1])
        else:
            zip9.append(row['zip-9-generated'])
    df2['zip-9-generated']=zip9
    df2.head()
    return df2



#Function to use the Census API to map the latitudes and longitudes to the FIPS-15(Census Blocks) and FIPS-11(Census Tract) values.
def coordinates_to_geoID(df1):
    print('Hi')
    census_block=[]
    census_tract=[]
    for idx, row in df1.iterrows():
        lat = row['coordinate_y']
        lng = row['coordinate_x']
        vintage='Census2020_Census2020'
        benchmark='Public_AR_Census2020'
        format = "json"

        endpoint = f"https://geocoding.geo.census.gov/geocoder/geographies/coordinates?x={lng}&y={lat}&benchmark={benchmark}&vintage={vintage}&format={format}"
        response = requests.get(endpoint)

        if response.status_code == 200:
                data = response.json()
                fips_code = data["result"]["geographies"]["Census Blocks"][0]["GEOID"]
                fips_code_tract=data["result"]["geographies"]["Census Tracts"][0]["GEOID"]
                census_block.append(fips_code)
                census_tract.append(fips_code_tract)
        else:
                census_block.append('NA')
                print(f"Request failed with status code {response.status_code}")
    df1['fips-15']=census_block
    df1['fips-11']=census_tract
    return df1


def google_api(df):
    df_chosen=df[df['score']<100]
    if len(df_chosen)<=100000:
        cost=0.005*len(df_chosen)
    else:
        cost=((0.005)*100000)+(len(df_chosen)-100000)*(0.4)
    print('The additional cost for using Google API is $'+str(cost))
    api_key='Insert your google api key here'
    zip9list_google=[]
    coordinate_x_google=[]
    coordinate_y_google=[]
    for idx, row in df_chosen.iterrows():
        flag=0
        if(row['score']<=99):
            address = str(row['Street']+', '+row['City']+', '+row['State'])

            url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}'

            # Send the request to the Geocoding API
            response = requests.get(url)
            data = response.json()
            if len(data['results'])>0:
                address_components = data['results'][0]['address_components']
                zip_code = ''
                zip_extension = ''
                for component in address_components:
                    if 'postal_code' in component['types']:
                        zip_code = component['short_name']

                    if 'postal_code_suffix' in component['types']:
                        zip_extension = component['short_name']
                        flag=1
                if flag==1:        
                    zip9list_google.append(zip_code+zip_extension)
                    y=data['results'][0]['geometry']['location']['lat']
                    x=data['results'][0]['geometry']['location']['lng']
                    coordinate_x_google.append(x)
                    coordinate_y_google.append(y)
        if flag==0:
            zip9list_google.append('')
            coordinate_x_google.append('')
            coordinate_y_google.append('')
    df_chosen['zip-9-generated-google-api']=zip9list_google
    df_chosen['coordinate_x_google_api']=coordinate_x_google
    df_chosen['coordinate_y_google_api']=coordinate_x_google
    intermediate_2= coordinates_to_geoID(df_chosen)
    return intermediate_2
    

#Main function that takes the input and output file as arguments to call the rest of the functions
def main(input_file, output_file, valid):
        df=pd.DataFrame(columns=['Street', 'City', 'State', 'zip-9-generated', 'coordinate_x', 'coordinate_y', 'zip-5'])
        IDR_DS=pd.read_csv(input_file)
        get_cost_arcGIS(IDR_DS)
        final_df=get_multiline_result(df, IDR_DS)
        final_df1=final_df.copy()
        intermediate_df= fill_PO_Box_addresses(final_df1)
        intermediate_2= coordinates_to_geoID(intermediate_df)
        intermediate_2.to_csv(output_file)
        if valid==True:
            final= google_api(intermediate_2)
            final.to_csv('.google.csv')
