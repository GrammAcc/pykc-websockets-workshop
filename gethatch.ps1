# Creates a minimal venv and installs hatch locally.

# Usage: `PS> ./gethatch.ps1`


python -m venv .venv
./.venv/Scripts/Activate.ps1
pip --require-virtualenv install hatch
