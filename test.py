import requests

url = 'http://localhost:5000/calculate_cost'
file = {'file': ('random_addresses.csv', open('random_addresses.csv', 'rb'), 'text/csv')}
response = requests.post(url, files=file)

print(response.text)