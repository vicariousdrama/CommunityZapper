from nostr.event import Event
from nostr.filter import Filter, Filters
from nostr.message_type import ClientMessageType
import json
import logging
import shutil
import sys
import time
import libfiles as files
import libnostr as nostr
import libutils as utils

def getCommunities() -> list[Event]:

    # retrieve events where, kind = 34550, posted by ownerPubkey, and d tag is the community id
    subscription_id = f"my_events"
    filter = Filter(kinds=[34550])
    filters = Filters([filter])
    nostr._relayManager.add_subscription(id=subscription_id, filters=filters)
    request = [ClientMessageType.REQUEST, subscription_id]
    request.extend(filters.to_json_array())
    message = json.dumps(request)
    nostr._relayManager.publish_message(message)
    time.sleep(nostr._relayPublishTime)
    nostr.siftMessagePool()
    nostr.removeSubscription(nostr._relayManager, subscription_id)

    # find the events
    events = nostr.popEventsMatchingFilter(filter)

    # sample for Outdoors community
    # {
    #     "id": "fec421b87c25c2f1ee959a000f680b5b50cabf0c17176b336e49d9b8d29e7dcc", 
    #     "pubkey": "026d8b7e7bcc2b417a84f10edb71b427fe76069905090b147b401a6cf60c3f27",
    #     "created_at": 1700460259, 
    #     "kind": 34550, 
    #     "tags": [
    #         ["d", "Outdoors"], 
    #         ["description", "Notes about nature, hiking, and outdoorsy stuff."], 
    #         ["image", "https://image.nostr.build/3a925e915f34b30eefbb981c0757cfdc09986afe4733acb32e2c08325e1ad7d9.jpg", "275x183"], 
    #         ["p", "026d8b7e7bcc2b417a84f10edb71b427fe76069905090b147b401a6cf60c3f27", "", "moderator"], 
    #         ["p", "21b419102da8fc0ba90484aec934bf55b7abcf75eedb39124e8d75e491f41a5e", "", "moderator"], 
    #         ["p", "c6cfec69543456207140127d93d69ea96d43f3c661948c1c9b7bb682c08b73b8", "", "moderator"], 
    #         ["relay", "wss://theforest.nostr1.com"]
    #     ], 
    #     "content": "", 
    #     "sig": "cd9b0161c5c924840cc781fb23d193afe9688c6cd2d4e3bae6a8dabef0b37918fd538c1ce0fd220a25afd830e137e2dbf2c7c15bd054ef2fd451cacca0bf2794"
    # }
    return events



if __name__ == '__main__':

    startTime, _ = utils.getTimes()

    # Logging to systemd
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt="%(asctime)s %(name)s.%(levelname)s: %(message)s", datefmt="%Y.%m.%d %H:%M:%S")
    stdoutLoggingHandler = logging.StreamHandler(stream=sys.stdout)
    stdoutLoggingHandler.setFormatter(formatter)
    logging.Formatter.converter = time.gmtime
    logger.addHandler(stdoutLoggingHandler)
    files.logger = logger
    nostr.logger = logger

    # Load server config
    config = files.getConfig(f"{files.dataFolder}config.json")
    if len(config.keys()) == 0:
        shutil.copy("sample-config.json", f"{files.dataFolder}config.json")
        logger.info(f"Copied sample-config.json to {files.dataFolder}config.json")
        logger.info("You will need to modify this file to setup nostr, lnd, and lnurl sections")
        quit()
    nostr.config = config["nostr"]

    nostr.connectToRelays()

    communityDefs = getCommunities()

    nostr.disconnectRelays()

    if len(communityDefs) == 0:
        logger.warning("No communities were found on relays.")
        quit()

    mkey = None
    mkeyCommunities = []
    if len(sys.argv) > 1: mkey = sys.argv[1]

    for communityDef in communityDefs:
        communityDTag = ""
        communityDescription = ""
        communityName = ""
        communityOwner = communityDef.public_key
        moderators = []
        for tagItem in communityDef.tags:
            if len(tagItem) < 2: continue
            if tagItem[0] == 'd': communityDTag = tagItem[1]
            if tagItem[0] == 'description': communityDescription = tagItem[1]
            if tagItem[0] == 'name': communityName = tagItem[1]
            if tagItem[0] == 'p': 
                 if len(tagItem) >= 4 and tagItem[3] == 'moderator':
                      moderators.append(tagItem[1])                          
        if len(communityName) == 0: communityName = communityDTag
        communityATag = f"34550:{communityOwner}:{communityDTag}"
        logger.debug("---")
        logger.debug(f"Community: {communityName}")
        logger.debug(f"  description: {communityDescription}")
        logger.debug(f"  owner:       {communityOwner}")
        logger.debug(f"  dTag:        {communityName}")
        logger.debug(f"  aTag:        {communityATag}")
        for moderator in moderators:
            logger.debug(f"  moderator:   {moderator}")
            if mkey is not None and mkey == moderator:
                mkeyCommunities.append(communityATag)
        
        if mkey is not None and len(mkeyCommunities) > 0:
            logger.debug("==============================================")
            logger.debug(f"Communities moderated by {mkey}")
            logger.debug("----------------------------------------------")
            for c in mkeyCommunities:
                logger.debug(c)

