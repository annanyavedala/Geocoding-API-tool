#To use the SDOH Mapping tool as an API, run this file.
#To run this file, run 'python3 main.py'
from flask import Flask, jsonify, request, send_file
import pandas as pd
from SDOHMappingTool import *
app = Flask(__name__)

@app.route('/calculate_cost', methods=['POST'])
def calculate_cost():
    file = request.files['file']
    df = pd.read_csv(file)
    cost = get_cost_arcGIS(df)
    return {'cost': cost}



@app.route('/calculateFIPS', methods=['POST'])
def calculateFIPS():
    df=pd.DataFrame(columns=['Street', 'City', 'State', 'zip-9-generated', 'coordinate_x', 'coordinate_y', 'zip-5'])
    file = request.files['file']
    IDR_DS=pd.read_csv(file)
    final_df=get_multiline_result(df, IDR_DS)
    final_df1=final_df.copy()
    intermediate_df= fill_PO_Box_addresses(final_df1)
    intermediate_2= coordinates_to_geoID(intermediate_df)
    intermediate_2.to_csv('new_data.csv')
    return send_file('new_data.csv', mimetype='text/csv', as_attachment=True)


@app.route('/google_api', methods=['POST'])
def calculateGoogleFIPS():
    

if __name__ == '__main__':
    app.run(debug=True)
