from logging.handlers import RotatingFileHandler
from nostr.event import Event
from nostr.filter import Filter, Filters
from nostr.message_type import ClientMessageType
import json
import logging
import random
import shutil
import sys
import time
import libfiles as files
import liblnd as lnd
import liblnurl as lnurl
import libnostr as nostr
import libutils as utils

def getCommunityDefinition(ownerPubkey: str, communityId: str):

    # retrieve events where, kind = 34550, posted by ownerPubkey, and d tag is the community id
    subscription_id = f"my_events_def_{communityId}"
    filter = Filter(kinds=[34550],authors=[ownerPubkey])
    filter.add_arbitrary_tag("d", [communityId])
    aTag = f"34550:{ownerPubkey}:{communityId}"
    #filter.add_arbitrary_tag("a", [aTag])
    filters = Filters([filter])
    nostr._relayManager.add_subscription(id=subscription_id, filters=filters)
    request = [ClientMessageType.REQUEST, subscription_id]
    request.extend(filters.to_json_array())
    message = json.dumps(request)
    nostr._relayManager.publish_message(message)
    time.sleep(nostr._relayPublishTime)
    nostr.siftMessagePool()
    nostr.removeSubscription(nostr._relayManager, subscription_id)

    # find the event
    definition = nostr.popEventMatchingFilter(filter)
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
    return definition

def getCommunityModeratorList(communityDef: Event):
    moderators = []
    if communityDef is not None:
        for tagItem in communityDef.tags:
            if len(tagItem) < 4: continue
            if tagItem[0] != 'p': continue
            if tagItem[3] != 'moderator': continue
            moderators.append(tagItem[1])
    return moderators

def getApprovedEvents(moderatorPubkey: str, communityATag: str, since: int, until: int):
    # retrieve events where, kind = 4550, posted by moderatorPubkey, and a tag is the communityATag
    t, _ = utils.getTimes()
    subscription_id = f"my_events_approved_{t}"
    filter = Filter(kinds=[4550],authors=[moderatorPubkey],since=since,until=until)
    filter.add_arbitrary_tag("a", [communityATag])
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
    # sample approval for the community. 
    # pubkey is the moderator that approved. 'e' tag is the original event approved, 'p' tag is original poster'
    # {
    #     "id": "aed68d67f15dd5295064afba46adc86e1cec2fc3629d564a833eedeec8016d6c", 
    #     "pubkey": "026d8b7e7bcc2b417a84f10edb71b427fe76069905090b147b401a6cf60c3f27", 
    #     "created_at": 1699254717, 
    #     "kind": 4550, 
    #     "tags": [
    #         ["a", "34550:026d8b7e7bcc2b417a84f10edb71b427fe76069905090b147b401a6cf60c3f27:Outdoors", "wss://greensoul.space"],
    #         ["e", "8202e7fcefbffed58249b5d56db3be6a9883dd39bb92bd235d72943ddf555c82"], 
    #         ["p", "21b419102da8fc0ba90484aec934bf55b7abcf75eedb39124e8d75e491f41a5e"], 
    #         ["k", "1"]
    #     ], 
    #     "content": "{\"content\":\"\\nThe only photo I took on the hike today. Also forgot my garmin.\\n\\nhttps://image.nostr.build/d48e738ff8e5e9d4b549aaf593ed5d09b88bad1c70bfadaf26b2f397aa8382e2.jpg\",\"created_at\":1699253110,\"id\":\"8202e7fcefbffed58249b5d56db3be6a9883dd39bb92bd235d72943ddf555c82\",\"kind\":1,\"pubkey\":\"21b419102da8fc0ba90484aec934bf55b7abcf75eedb39124e8d75e491f41a5e\",\"sig\":\"f232128e86da7825a90e8f878fd96b503e9388e3846a1732dd0971418a3dc699616a4b207c6bcb002a9f7b569a18a7751520bf836612a11522351e7fa3e9b941\",\"tags\":[[\"a\",\"34550:026d8b7e7bcc2b417a84f10edb71b427fe76069905090b147b401a6cf60c3f27:Outdoors\",\"\",\"reply\"],[\"r\",\"https://image.nostr.build/d48e738ff8e5e9d4b549aaf593ed5d09b88bad1c70bfadaf26b2f397aa8382e2.jpg\"]]}", 
    #     "sig": "ded4197d45b1fe473dba96c72124558a47497001462b884088f287fc22eccd223b5247f0b03cf657da9cc740f32e93d82285cdb826f2cb5c1eb548bed0d1e3cf"
    # }
    return events

def parseIDs(event: Event):
    pubkey = None
    id = None
    for tagItem in event.tags:
        if len(tagItem) < 2: continue
        if tagItem[0] == 'e' and id is None: id = tagItem[1]
        if tagItem[0] == 'p' and pubkey is None: pubkey = tagItem[1]
    return pubkey, id

def getZapFields(pubkey, amount):
    callback = None
    bech32lnurl = None
    errMessage = None
    lightningId, name = nostr.getLightningIdForPubkey(pubkey)
    valid, errMessage = nostr.isValidLightningId(lightningId)
    if valid:
        lnurlPayInfo, lnurlp = lnurl.getLNURLPayInfo(lightningId)
        if lnurl.isLNURLProviderAllowed(lightningId):
            callback, bech32lnurl, errMessage = nostr.validateLNURLPayInfo(
                lnurlPayInfo, lnurlp, lightningId, name, amount, pubkey)
            if not lnurl.isLNURLCallbackAllowed(callback):
                errMessage = "Callback not allowed"
        else:
            errMessage = "Provider not allowed"
    return lightningId, name, callback, bech32lnurl, errMessage

def payZap(zapRequest, amount, callback, bech32lnurl):
    zapped = False
    invoice = lnurl.getInvoiceFromZapRequest(callback, amount, zapRequest, bech32lnurl)
    if not lnurl.isValidInvoiceResponse(invoice): 
        return zapped, "INVALID INVOICE"
    paymentRequest = invoice["pr"]
    decodedInvoice = lnd.decodeInvoice(paymentRequest)
    if decodedInvoice is None:
        return zapped, f"COULD NOT GET DECODED INVOICE from {paymentRequest}"
    lnd.recordPaymentDestination(decodedInvoice)
    if not lnurl.isValidInvoiceAmount(decodedInvoice, amount): return zapped, "INVALID AMOUNT"
    paymentTime, paymentTimeISO = utils.getTimes()
    paymentStatus, paymentFees, paymentHash, paymentIndex = lnd.payInvoice(paymentRequest)
    # todo: for a paid service, this would need to track all paid amounts and follow up on payment status
    zapped = True
    return zapped, paymentStatus

def getCommunityFolder(communityATag):
    parts = communityATag.split(":")
    name = parts[2]
    pubkey = parts[1]
    communityFolder = f"{files.dataFolder}communities/{name}/{pubkey}/"
    return communityFolder

def recordPayment(purpose, communityATag, pubkey, approvedPostID, amount):
    if communityATag is None: return
    communityName = communityATag.split(":")[2]
    filePayments = f"{communityFolder}payments.json"
    payments = files.loadJsonFile(filePayments, [])
    payments.append({"purpose":purpose,"community":communityName,"pubkey":pubkey,"postid":approvedPostID,"amount":amount})
    files.saveJsonFile(filePayments, payments)

def zapPost(communityATag, approvedPostPubkey, approvedPostID, amount, comment):
    if communityATag is None: return
    if approvedPostPubkey is None: return
    if approvedPostID is None: return
    communityName = communityATag.split(":")[2]
    communityFolder = getCommunityFolder(communityATag)
    filePosts = f"{communityFolder}zappedposts.json"
    # {"pubkey1": ["postA","postD"],"pubkey2":["postB"],"pubkey3":["postC"]}
    posts = files.loadJsonFile(filePosts, {})
    pubkeyPosts = [] if approvedPostPubkey not in posts.keys() else posts[approvedPostPubkey]
    if approvedPostID in pubkeyPosts:
        # already zapped, dont zap again
        logger.debug("- skipping post zapped previously")
        return
    
    lightningId,name,callback,bech32lnurl,errMessage = getZapFields(approvedPostPubkey, amount)
    if lightningId is None or name is None or callback is None or bech32lnurl is None or errMessage is not None:
        logger.debug(f"- skipping zap due to error: {errMessage}")
        logger.debug(f"  lightningId: {lightningId}")
        logger.debug(f"  name: {name}")
        logger.debug(f"  callback: {callback}")
        logger.debug(f"  bech32lnurl: {bech32lnurl}")
        return
    zapRequest = nostr.makeZapRequest(
        nostr.getPrivateKey(), 
        amount, 
        comment, 
        approvedPostPubkey, 
        approvedPostID, 
        bech32lnurl)
    logger.debug(f"- zapping post by {name} ({lightningId}) {amount} sats in community {communityName}")
    wasZapped, paymentStatus = payZap(zapRequest, amount, callback, bech32lnurl)
    if not wasZapped: 
        logger.debug(f"- post wasn't zapped due to error: {paymentStatus}")

    recordPayment("zapped post", communityATag, approvedPostPubkey, approvedPostID, amount)

    # save it
    pubkeyPosts.append(approvedPostID)
    posts[approvedPostPubkey] = pubkeyPosts
    files.saveJsonFile(filePosts, posts)

def zapModerator(communityATag: str, moderator: str, approvalEventId: str, approvedPostID: str, amounts: list, comment: str):
    if communityATag is None: return
    if moderator is None: return
    if approvalEventId is None: return
    if approvedPostID is None: return
    communityName = communityATag.split(":")[2]
    communityFolder = getCommunityFolder(communityATag)
    filePosts = f"{communityFolder}zappedmoderators.json"
    # {"postA": ["moderator1", "moderator2"], "postB": ["moderator2"]}
    posts = files.loadJsonFile(filePosts, {})
    moderators = [] if approvalEventId not in posts.keys() else posts[approvalEventId]
    if moderator in moderators:
        # already zapped, dont zap again
        logger.debug("- skipping approval zapped previously")
        return
    # determine amount to zap based on array (earlier moderators generally rewarded more)
    amountIdx = len(moderators)
    amount = amounts[amountIdx] if amountIdx < len(amounts) else amounts[-1]

    lightningId,name,callback,bech32lnurl,errMessage = getZapFields(moderator, amount)
    if lightningId is None or name is None or callback is None or bech32lnurl is None or errMessage is not None:
        logger.debug(f"- skipping zap due to error: {errMessage}")
        logger.debug(f"  lightningId: {lightningId}")
        logger.debug(f"  name: {name}")
        logger.debug(f"  callback: {callback}")
        logger.debug(f"  bech32lnurl: {bech32lnurl}")
        return
    zapRequest = nostr.makeZapRequest(
        nostr.getPrivateKey(), 
        amount, 
        comment, 
        moderator, 
        approvalEventId, 
        bech32lnurl)
    logger.debug(f"- zapping moderator {name} ({lightningId}) {amount} sats for approving post in community {communityName}")
    wasZapped, paymentStatus = payZap(zapRequest, amount, callback, bech32lnurl)
    if not wasZapped: 
        logger.debug(f"- post wasn't zapped due to error: {paymentStatus}")

    recordPayment("zapped moderator", communityATag, moderator, approvedPostID, amount)

    # save it
    moderators.append(moderator)
    posts[approvalEventId] = moderators
    files.saveJsonFile(filePosts, posts)

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
    logFile = f"{files.logFolder}communityzapper.log"
    fileLoggingHandler = RotatingFileHandler(logFile, mode='a', maxBytes=10*1024*1024, 
                                 backupCount=21, encoding=None, delay=0)
    fileLoggingHandler.setFormatter(formatter)
    logger.addHandler(fileLoggingHandler)
    files.logger = logger
    lnd.logger = logger
    lnurl.logger = logger
    nostr.logger = logger

    # Load server config
    config = files.getConfig(f"{files.dataFolder}config.json")
    if len(config.keys()) == 0:
        shutil.copy("sample-config.json", f"{files.dataFolder}config.json")
        logger.info(f"Copied sample-config.json to {files.dataFolder}config.json")
        logger.info("You will need to modify this file to setup nostr, lnd, and lnurl sections")
        quit()
    nostr.config = config["nostr"]
    lnd.config = config["lnd"]
    lnurl.config = config["lnurl"]

    # Load Lightning ID cache
    nostr.loadLightningIdCache()

    monitordefs = nostr.config["monitor"]
    if len(monitordefs) == 0:
        logger.warning("No communities being monitored. Add definitions to monitor field in nostr section of config.json")
        quit()

    duration1hour = 1 * 60 * 60
    while True:

        nostr.connectToRelays()

        for monitordef in monitordefs:
            randomZapEnabled = False
            randomZap = 0
            if "enabled" in monitordef:
                if not monitordef["enabled"]:
                    continue
            # 2023-01-01    1672531200
            # 2023-12-01    1701388800
            since = 1701388800
            until, _ = utils.getTimes()
            if "since" in monitordef: since = monitordef["since"]
            if "until" in monitordef: until = monitordef["until"]
            if "randomZap" in monitordef: randomZap = monitordef["randomZap"]
            ownerPubkey = monitordef["owner"]
            communityID = monitordef["dTag"]
            logger.debug(f"Processing {communityID} by {ownerPubkey}")
            zapModerators = [21] if "zapModerators" not in monitordef else monitordef["zapModerators"]
            zapModeratorMsg = "Thanks for moderating!" if "zapModeratorMsg" not in monitordef else monitordef["zapModeratorMsg"]
            zapContributors = 21 if "zapContributors" not in monitordef else monitordef["zapContributors"]
            zapContributorMsg = "Thanks for sharing with the community!" if "zapContributorMsg" not in monitordef else monitordef["zapContributorMsg"]
            communityATag = f"34550:{ownerPubkey}:{communityID}"
            communityFolder = getCommunityFolder(communityATag)
            utils.makeFolderIfNotExists(communityFolder)
            communityDef = getCommunityDefinition(ownerPubkey, communityID)
            moderators = getCommunityModeratorList(communityDef)
            for moderator in moderators:
                approvalEvents = getApprovedEvents(moderator, communityATag, since, until)
                approvalCount = len(approvalEvents)
                logger.debug(f"- {approvalCount} approved events by {moderator}")
                for approvalEvent in approvalEvents:
                    approvedPostPubkey, approvedPostID = parseIDs(approvalEvent)
                    zapAmount = zapContributors
                    if randomZapEnabled:
                        if random.randint(1,21) == 21:
                            logger.debug(f"Random Hit! Changing amount to {randomZap}")
                            zapAmount = randomZap
                    zapPost(communityATag, approvedPostPubkey, approvedPostID, zapAmount, zapContributorMsg)
                    if moderator != approvedPostPubkey:
                        zapAmounts = zapModerators
                        if random.randint(1,21) == 21:
                            logger.debug(f"Random Hit! Changing amount to {randomZap}")
                            zapAmounts = [randomZap]
                        zapModerator(communityATag, moderator, approvalEvent.id, approvedPostID, zapAmounts, zapModeratorMsg)
            logger.debug(f"- done checking {communityID}")

        nostr.disconnectRelays()

        logger.debug(f"Sleeping {duration1hour} seconds")
        time.sleep(duration1hour)
