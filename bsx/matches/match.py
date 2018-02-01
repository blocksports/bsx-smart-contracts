from boa.blockchain.vm.Neo.Blockchain import GetHeight
from boa.blockchain.vm.Neo.Action import RegisterAction
from boa.blockchain.vm.Neo.Runtime import Notify,CheckWitness
from boa.code.builtins import concat, sha1
from bsx.common.utils import ValidateArgsLength, GetCurrentTimestamp
from nex.common.storage import StorageAPI

class Match():

    match_prefix = b'match/'

    time_buffer = 300

    storage = StorageAPI()

    def ValidateActiveMatch(self, args):
        storage = StorageAPI()

        isValidLength = ValidateArgsLength(args, 1)
        if isValidLength == False:
            return False    
        
        matchID = args[0]

        matchKey = concat(self.match_prefix, matchID)
        
        match = storage.get(matchKey)

        if match != "active":
            msg1 = concat("Match status is: ", match)
            msg2 = ", Expected status to be: active"
            msg = concat(msg1, msg2)
            Log(msg)

            return False            

        startKey = concat(matchKey, "/start")
        startTime = storage.get(startKey)
        currentTime = GetCurrentTimestamp()

        if currentTime > startTime - self.time_buffer:
            Log("Betting is suspended for this match")
            return False

        return True

    def CheckMatchOutcome(self, args):
        storage = StorageAPI()

        isValidLength = ValidateArgsLength(args, 1)
        if isValidLength == False:
            return False    

        matchID = args[0]

        matchKey = concat(self.match_prefix, matchID)
        
        match = storage.get(matchKey)

        if match == "void":
            return match

        elif match != "finished":
            msg1 = concat("Match status is: ", match)
            msg2 = ", Expected status to be: finished"
            msg = concat(msg1, msg2)
            Log(msg)

            return False

        outcomeKey = concat(matchKey, "/outcome")
        finalOutcome = storage.get(outcomeKey) 

        return finalOutcome  

# Not finalised whether we store all match details on chain or just the core details
def CreateMatchID(details): 
    # Saves a few hundred ops doing this manually
    name = details[0]
    sport = details[1]
    comp = details[2]
    participants = details[3]
    start = details[4]
    numOutcomes = details[5]
    canDraw = details[6]

    rawMatchID = concat(name, sport)
    rawMatchID = concat(rawMatchID, comp)
    rawMatchID = concat(rawMatchID, participants)
    rawMatchID = concat(rawMatchID, start)
    rawMatchID = concat(rawMatchID, numOutcomes)
    rawMatchID = concat(rawMatchID, canDraw)

    matchID = sha1(rawMatchID)
    
    return matchID  

def StoreMatchDetails(storage:StorageAPI, matchKey, details):
    start = details[4]
    numOutcomes = details[5]
    canDraw = details[6]

    startKey = concat(matchKey, "/start")
    numOutcomesKey = concat(matchKey, "/num_outcomes")
    drawKey = concat(matchKey, "/draw")

    storage.put(matchKey, "pending")
    storage.put(startKey, start)
    storage.put(numOutcomesKey, numOutcomes)
    storage.put(drawKey, canDraw)

    return