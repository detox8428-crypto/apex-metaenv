import sys
print('Python path:')
for p in sys.path[:5]:
    print(f'  {p}')

# Try to import server again to see what happens
try:
    import server
    print(f'\nserver module location: {server.__file__}')
    print(f'server.app: {server.app}')
    print(f'server.app.__class__: {server.app.__class__}')
    
    # Check if it's the same app
    from fastapi import FastAPI
    print(f'Is FastAPI app: {isinstance(server.app, FastAPI)}')
    
    # Print routes
    print(f'\nRoutes in server.app:')
    for route in server.app.routes[:15]:
        print(f'  {getattr(route, "path", "?")}')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
