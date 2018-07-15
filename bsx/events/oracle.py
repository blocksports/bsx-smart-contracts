from boa.blockchain.vm.Neo.Action import RegisterAction
from boa.code.builtins import concat, sha1 
from bsx.events.event import CreateEventID, StoreEventDetails
from bsx.common.utils import ValidateArgsLength
from nex.common.storage import StorageAPI

OnNewEventAdded = RegisterAction("new_event_added", "event_id", "oracle_id", "event_details")
OnNewEventConsensus = RegisterAction("new_event_consensus", "event_id", "oracle_id")
OnNewEventConfirmed = RegisterAction("new_event_confirmed", "event_id", "oracle_id")

OnEventOutcomeConsensus = RegisterAction("update_event_consensus", "event_id", "outcome", "oracle_id")
OnEventOutcomeConfirmed = RegisterAction("update_event_confirmed", "event_id", "outcome", "oracle_id")

class Oracle():

    event_prefix = b'event/'
    oracle_prefix = b'oracle/'

    outcome_oracle_prefix = b'outcome_oracle/'
    outcome_count_prefix = b'outcome_count/'

    oracle_count_key = b'oracle/count'
    oracle_consensus_key = b'oracle/consensus'

    def AddEvent(self, args, oracleID):
        storage = StorageAPI()

        isValidSender = self.ValidateOracle(storage, oracleID)
        if isValidSender == False:
            return False

        isValidLength = ValidateArgsLength(args, 7)
        if isValidLength == False:
            return False

        eventID = CreateEventID(args)

        eventKey = concat(self.event_prefix, eventID)
        event = storage.get(eventKey)

        if event == False:
            _ = StoreEventDetails(storage, eventKey, args)

            event = "pending"

            OnNewEventAdded(eventID, oracleID, args)
            
        if event == "pending":
            oracleKey = concat(eventKey, oracleID) 
            countKey = concat(eventKey, "/count")

            reachedConsensus = self.CheckEventConsensus(storage, oracleKey, countKey)

            if reachedConsensus == False:
                OnNewEventConsensus(eventID, oracleID)
            
            else: 
                storage.put(eventKey, "active")

                OnNewEventConfirmed(eventID, oracleID)
                
            return  True
        else:
            msg1 = concat("Consensus has finished for: ", eventID)
            msg2 = concat(", Event state is currently: ", event)
            msg = concat(msg1, msg2)

            Log(msg)

        return False

    def UpdateEventOutcome(self, args, oracleID):
        storage = StorageAPI()

        isValidSender = self.ValidateOracle(storage, oracleID)
        if isValidSender == False:
            return False

        isValidLength = ValidateArgsLength(args, 2)
        if isValidLength == False:
            return False    

        eventID = args[0]
        outcome = args[1]

        eventKey = concat(self.event_prefix, eventID)
        event = storage.get(eventKey)    

        if event != "active":
            msg1 = concat("Cannot update event: ", eventID)
            msg2 = concat(", Event state is currently: ", event)
            msg = concat(msg1, msg2)

            Log(msg)

            return False
        
        oracleSuffix = concat(self.outcome_oracle_prefix, oracleID)
        countSuffix = concat(self.outcome_count_prefix, outcome)

        oracleKey = concat(eventKey, oracleSuffix)   
        countKey = concat(eventKey, countSuffix)

        reachedConsensus = self.CheckEventConsensus(storage, oracleKey, countKey)

        if reachedConsensus == False:
                OnEventOutcomeConsensus(eventID, oracleID)
            
        else: 
            if outcome == "void":
                storage.put(eventKey, "void")

            else: 
                outcomeKey = concat(eventKey, "/outcome")

                storage.put(outcomeKey, outcome)
                storage.put(eventKey, "finished")


            OnEventOutcomeConfirmed(eventID, outcome, oracleID)

        return True

    def ValidateOracle(self, storage:StorageAPI, oracleID):
        isOracle = CheckWitness(oracleID)
        if isOracle == False:
            msg = concat("Given address is not the sender: ", oracleID)
            Log(msg)
            return False

        return True

    def CheckEventConsensus(self, storage:StorageAPI, oracleKey, countKey):
        oracleStatus = storage.get(oracleKey)
        if oracleStatus == "participated":
            Log("Oracle has already participated")
            return False

        count = storage.get(countKey)
        newCount = count + 1

        storage.put(countKey, newCount)
        storage.put(oracleKey, "participated")
        
        oracleCount = storage.get(self.oracle_count_key)
        consensusRequired = storage.get(self.oracle_consensus_key)

        factoredCount = newCount * 100
        required = oracleCount * consensusRequired

        return factoredCount >= required


