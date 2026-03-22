Write-Host ""
Write-Host "==============================="
Write-Host " DiffInsight Dev Environment"
Write-Host "==============================="
Write-Host ""

# Activate environment
conda activate diffinsight

# Vault config
$env:VAULT_ADDR="http://127.0.0.1:8200"

$vaultToken = Read-Host "Paste Vault Root Token"
$env:VAULT_TOKEN=$vaultToken

# Check GitHub token
vault kv get secret/github > $null 2>&1

if ($LASTEXITCODE -ne 0) {

    Write-Host "GitHub token missing in Vault."

    $gh = Read-Host "Paste GitHub PAT"

    vault kv put secret/github token=$gh

}

Write-Host ""
Write-Host "Testing Vault connection..."

python test_env.py

Write-Host ""
Write-Host "Starting FastAPI..."

uvicorn backend.main:app --reload