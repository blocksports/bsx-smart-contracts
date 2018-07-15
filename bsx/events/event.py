from boa.blockchain.vm.Neo.Blockchain import GetHeight
from boa.blockchain.vm.Neo.Action import RegisterAction
from boa.blockchain.vm.Neo.Runtime import Notify,CheckWitness
from boa.code.builtins import concat, sha1
from bsx.common.utils import ValidateArgsLength, GetCurrentTimestamp
from nex.common.storage import StorageAPI

class Event():

    event_prefix = b'event/'

    time_buffer = 300

    storage = StorageAPI()

    def ValidateActiveEvent(self, args):
        storage = StorageAPI()

        isValidLength = ValidateArgsLength(args, 1)
        if isValidLength == False:
            return False    
        
        eventID = args[0]

        eventKey = concat(self.event_prefix, eventID)
        
        event = storage.get(eventKey)

        if event != "active":
            msg1 = concat("Event status is: ", event)
            msg2 = ", Expected status to be: active"
            msg = concat(msg1, msg2)
            Log(msg)

            return False            

        startKey = concat(eventKey, "/start")
        startTime = storage.get(startKey)
        currentTime = GetCurrentTimestamp()

        if currentTime > startTime - self.time_buffer:
            Log("Betting is suspended for this event")
            return False

        return True

    def CheckEventOutcome(self, args):
        storage = StorageAPI()

        isValidLength = ValidateArgsLength(args, 1)
        if isValidLength == False:
            return False    

        eventID = args[0]

        eventKey = concat(self.event_prefix, eventID)
        
        event = storage.get(eventKey)

        if event == "void":
            return event

        elif event != "finished":
            msg1 = concat("Event status is: ", event)
            msg2 = ", Expected status to be: finished"
            msg = concat(msg1, msg2)
            Log(msg)

            return False

        outcomeKey = concat(eventKey, "/outcome")
        finalOutcome = storage.get(outcomeKey) 

        return finalOutcome  

# Not finalised whether we store all event details on chain or just the core details
def CreateEventID(details): 
    # Saves a few hundred ops doing this manually
    name = details[0]
    sport = details[1]
    competition = details[2]
    home = details[3]
    away = details[4]
    start = details[5]
    canDraw = details[6]

    rawEventID = concat(name, sport)
    rawEventID = concat(rawEventID, competition)
    rawEventID = concat(rawEventID, home)
    rawEventID = concat(rawEventID, away)
    rawEventID = concat(rawEventID, start)
    rawEventID = concat(rawEventID, canDraw)

    eventID = sha1(rawEventID)
    
    return eventID  

def StoreEventDetails(storage:StorageAPI, eventKey, details):
    start = details[5]
    canDraw = details[6]

    startKey = concat(eventKey, "/start")
    drawKey = concat(eventKey, "/draw")

    storage.put(eventKey, "pending")
    storage.put(startKey, start)
    storage.put(drawKey, canDraw)

    return