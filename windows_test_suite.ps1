Write-Output "Starting test server in background..."
$svjob = Start-Job {hypercorn windows_test_app.py}
sleep 1
Write-Output "Running test suite..."
pytest
Write-Output "Shutting down test server and cleaning up background process..."
Stop-Job $svjob
Remove-Job $svjob
Write-Output "Run complete!"
