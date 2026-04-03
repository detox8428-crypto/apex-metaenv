import requests
import json

base_url = 'http://localhost:8000'

# Get OpenAPI schema
print('Fetching OpenAPI schema...')
response = requests.get(f'{base_url}/openapi.json')
print(f'Status: {response.status_code}')

if response.status_code == 200:
    schema = response.json()
    print(f'\nOpenAPI Info:')
    print(f'  Title: {schema.get("info", {}).get("title")}')
    print(f'  Version: {schema.get("info", {}).get("version")}')
    
    paths = list(schema.get('paths', {}).keys())
    print(f'\nPaths ({len(paths)}):')
    for path in sorted(paths):
        methods = list(schema['paths'][path].keys())
        print(f'  {path:20} {methods}')
else:
    print(f'Error: {response.text}')
