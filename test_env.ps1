$env:API_BASE_URL = "https://router.huggingface.co/v1"
$env:API_KEY = "hf_test_key_placeholder"
$env:MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct"

Write-Host "[ENV CHECK]" -ForegroundColor Green
Write-Host "API_BASE_URL=$($env:API_BASE_URL)"
Write-Host "API_KEY=$($env:API_KEY)"
Write-Host "MODEL_NAME=$($env:MODEL_NAME)"
Write-Host ""
Write-Host "[IMPORT CHECK]" -ForegroundColor Green

python -c "
import os
import sys

print('Python version:', sys.version.split()[0])
print('API_BASE_URL:', os.environ.get('API_BASE_URL'))
print('API_KEY:', os.environ.get('API_KEY'))
print('MODEL_NAME:', os.environ.get('MODEL_NAME'))
print()

try:
    from openai import OpenAI
    print('✓ OpenAI import successful')
    
    # Try to create client with env vars
    API_BASE_URL = os.environ['API_BASE_URL']
    API_KEY = os.environ['API_KEY']
    
    client = OpenAI(
        base_url=API_BASE_URL,
        api_key=API_KEY,
    )
    print('✓ OpenAI client initialized successfully')
    print('✓ Ready for API calls')
except Exception as e:
    print('✗ Error:', str(e))
    sys.exit(1)
"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[SUCCESS]" -ForegroundColor Green
    Write-Host "Environment is configured correctly!"
    Write-Host ""
    Write-Host "To run the full benchmark, use:"
    Write-Host "python inference.py"
} else {
    Write-Host ""
    Write-Host "[FAILED]" -ForegroundColor Red
    Write-Host "Configuration issues detected"
}
