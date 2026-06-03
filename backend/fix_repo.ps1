# Delete nested repository if it exists
if (Test-Path ".\fomc-ai-analyzer") {
    Remove-Item -Recurse -Force ".\fomc-ai-analyzer"
    Write-Host "Deleted nested repository folder."
}

# Create .gitignore
@"
venv/
__pycache__/
*.pyc
"@ | Out-File -Encoding utf8 .gitignore

Write-Host ".gitignore created."

# Remove cached git files if any
git rm --cached -r . 2>$null

# Add files again
git add .

Write-Host "Git staging fixed."