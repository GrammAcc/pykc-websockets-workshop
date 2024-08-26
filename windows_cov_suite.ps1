Write-Output "Starting test server in background..."
$svjob = Start-Job {hypercorn windows_test_app.py}
sleep 1
Write-Output "Collecting test coverage..."
pytest --cov-config=pyproject.toml --cov-report html:htmlcov --cov=pykcworkshop
Write-Output "Shutting down test server and cleaning up background process..."
Stop-Job $svjob
Remove-Job $svjob
Write-Output "Run complete!"
