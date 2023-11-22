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

## Configuration

There are three configuration segments in the config.json file.  You can copy the sample-config.json to the data/ folder as config.json to start with.

### Nostr Configuration

The `nostr` configuration section has these keys

| key | description |
| --- | --- |
| nsec | The nsec for the identity that will be doing the zapping |
| relays | The list of relays to use |
| monitor | Definitions for communities to monitor and zap parameters for posters and moderators |

The most critical to define here is the `nsec`.  You should generate an nsec on your own.

The `relays` is an array of relay definition where each has a `url`, `read` and `write` field.  The `url` is the websocket or secure websocket endpoint for the relay. The `read` and `write` fields indicate whether they should be used for reading or writing events from that relay

The `monitor` value is another array of definitions representing the communities to monitor and reward.  Each has fields as follows

- owner: the pubkey in hex format of the owner/creator of the community
- dTag: the community identifier referenced in the `d` tag.
- zapModerators: an array of amounts to zap moderators based on how many moderators have approved the event. In general, a progressively descending amount is suitable, which incentivizes moderators to approve earlier then others. If there are more moderators approving a post then there are amounts, then those moderators just get the last number in the list.
- zapModeratorMsg: a message to send to the moderator when zapping them
- zapContributors: An amount to zap a poster of a note in the community when their note is approved by a moderator
- zapContributorMsg: a message to send the pubkey that posted the originating note

A common challenge you may face is identifying the owner pubkey and dTag for a Community you want to reward with zaps.

If you have the user's npub, you can get the hex format by running the following, replacing my sample npub with that of the user you want to use (all on one line)

```sh
~/.pyenv/communityzapper/bin/python -c 'import libutils; print(libutils.normalizeToHex("npub1yx6pjypd4r7qh2gysjhvjd9l2km6hnm4amdnjyjw3467fy05rf0qfp7kza"))'
```

you may be able to get the dTag and owner npub for communities by using some of the following web clients:
- https://nostrudel.ninja
- https://satellite.earth


### Lightning Configuration

The `lnd` configuration section has these keys

| key | description |
| --- | --- |
| address | Where to reach the LND server |
| port | The listening port for LND server for GRPC REST calls |
| macaroon | The macaroon for authentication and authorization for the LND server in hex format |
| paymentTimeout | The time allowed in seconds to complete a payment or expire it |
| feeLimit | The maximum amount to allow for routing fees for each payment, in sats |
| connectTimeout | Time permitted in seconds to connect to LND |
| readTimeout | Time permitted in seconds to read all data from LND |
| activeServer | Optional name of a nested LND server configuration to use |
| servers | Optional object containing LND server configurations |

The `address` should be the ip address or fully qualified domain name to communicate with the LND server over REST

The `port` is the port the LND server is listening on for REST

The `macaroon` should be provided in hex format. 

The permissions needed are

- lnrpc.Lightning/DecodePayReq
- routerrpc.Router/SendPaymentV2
- routerrpc.Router/TrackPaymentV2
- lnrpc.Lightning/AddInvoice
- invoicesrpc.Invoices/LookupInvoiceV2

You can bake the macaroon as follows before convertng to hex.
```sh
lncli bakemacaroon uri:/lnrpc.Lightning/DecodePayReq uri:/routerrpc.Router/SendPaymentV2 uri:/routerrpc.Router/TrackPaymentV2 uri:/lnrpc.Lightning/AddInvoice uri:/invoicesrpc.Invoices/LookupInvoiceV2 --save_to ${HOME}/CommunityZapper.macaroon

cat ${HOME}/CommunityZapper.macaroon | xxd -p -c 1000
```

The `paymentTimeout` is the number of seconds that should be allowed for the payment to complete routing.  This helps avoid unnecessarily long in flights locking up funds.

The `feeLimit` is the maximum amount of fees, in sats, that you are willing to pay per zap performed, in addition to the amount being zapped.

The `connectTimeout` is the number of seconds to allow for making a connection to LND.

The `readTimeout` is the number of seconds to allow reading all data from LND.

The `activeServer` is an optional parameter whose value indicates the key name that should exist within the optional servers json object.

The `servers` field is an optional object that may contain nested LND server configurations that override the default values above when present and specified in the activeServer field.

The LND server needs to be reachable from where the script is run.

### LN Url Providers Configuration

The `lnurl` configuration section has these keys

| key | description |
| --- | --- |
| connectTimeout | Time permitted in seconds to connect to LN Url Providers |
| readTimeout | Time permitted in seconds to read all data from LN Url Providers |
| denyProviders | An optional list of domains hosting LN URL Providers that will not receive payouts |

The `connectTimeout` is the number of seconds to allow for making a connection to a LN Url Provider.

The `readTimeout` is the number of seconds to allow reading all data from a LN Url Provider.

The `denyProviders` is an array of strings containing entries of domain names for LN Url Providers that should not receive zaps even if they support it. This is helpful to exclude domains that are problematic with respect to HTLCs and may result in channel closures or loss of funds.

## Running the Bot

Once configured, run the bot using the previously established virtual environment

```sh
~/.pyenv/communityzapper/bin/python communityzapper.py
```