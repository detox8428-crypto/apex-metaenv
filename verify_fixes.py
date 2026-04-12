#!/usr/bin/env python3
import yaml

with open('openenv.yaml') as f:
    d = yaml.safe_load(f)

print('✓ openenv.yaml Verification:')
print(f'  type: {d.get("type")} (expected: space)')
print(f'  runtime: {d.get("runtime")} (expected: fastapi)')
print(f'  app: {d.get("app")} (expected: app:app)')
print(f'  tasks count: {len(d.get("tasks", []))} (expected: 9)')

readme = open('README.md', encoding='utf-8').read()
print()
print('✓ README.md Verification:')
print(f'  Contains "29 tasks": {"29 tasks" in readme} (expected: False)')
print(f'  Contains "9 tasks": {"9 tasks" in readme} (expected: True)')

all_pass = (
    d.get('type') == 'space' and 
    d.get('runtime') == 'fastapi' and 
    d.get('app') == 'app:app' and 
    len(d.get('tasks', [])) == 9 and
    '29 tasks' not in readme and
    '9 tasks' in readme
)
print()
print('STATUS: ' + ('✅ ALL CHECKS PASSED' if all_pass else '❌ SOME CHECKS FAILED'))
