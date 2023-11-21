# Community Zapper

This script monitors a defined list of communities and will zap moderators and users who post notes in the communities that are approved.

## Preparation of Python Environment

To use this script, you'll need to run it with python 3.9 or higher and with the nostr, requests and bech32 packages installed.

First, create a virtual environment (or activate a common one)

```sh
python3 -m venv ~/.pyenv/communityzapper
source ~/.pyenv/communityzapper/bin/activate
```

Then install the dependencies
```sh
python3 -m pip install nostr@git+https://github.com/vicariousdrama/python-nostr.git
python3 -m pip install requests
python3 -m pip install bech32
python3 -m pip install boto3
```