"""This script will (re)create the local environment settings used by the appliation.

Warning: This script will overwrite any changes you've made to the `.env` and `server.toml`
files, so you should only run this when setting up the initial environment, or in a CI pipeline.

The default settings assume local HTTP, so if you want to use local HTTPS, you will need
to change the `SITE_ROOT` from http to https in the `.env` file and uncomment the three lines
added to the `server.toml` file after generating the certs.
"""

import secrets

envlines = [
    f"JWT_SECRET={secrets.token_hex(16)}",
    f"QUART_SECRET={secrets.token_hex(16)}",
    "SITE_ROOT=http://localhost:8000",
    "LOG_LEVEL=DEBUG",
]
serverlines = [
    '# certfile = "certs/pykcworkshop.pem"',
    '# keyfile = "certs/pykcworkshop-key.pem"',
    '# ca-cert = "certs/rootCA.pem"',
]

with open(".env", "w") as file:
    file.write("\n".join(envlines))

with open("server.toml", "w") as file:
    file.write("\n".join(serverlines))
