import requests

base_url = 'http://localhost:8001'

print('Testing endpoints on port 8001:')
print('='*50)

# Test /health
print('GET /health:', end=' ')
r = requests.get(f'{base_url}/health')
print(f'{r.status_code}', end=' ')
print(r.json())

# Test /reset
print('POST /reset:', end=' ')
r = requests.post(f'{base_url}/reset', json={'seed': 42})
print(f'{r.status_code}')

# Test /openapi.json
print('GET /openapi.json:', end=' ')
r = requests.get(f'{base_url}/openapi.json')
schema = r.json()
title = schema.get('info', {}).get('title')
print(f'Title: {title}')

paths = list(schema.get('paths', {}).keys())
print(f'\nEndpoints: {sorted(paths)}')
