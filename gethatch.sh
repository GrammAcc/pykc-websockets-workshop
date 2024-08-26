# Creates a minimal venv and installs hatch locally.

# Usage: `source gethatch`

python -m venv .venv
source .venv/bin/activate
pip --require-virtualenv install hatch
