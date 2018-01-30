from boa.blockchain.vm.Neo.Action import RegisterAction
from boa.code.builtins import concat, sha1 
from bsx.matches.match import CreateMatchID, StoreMatchDetails
from bsx.common.utils import ValidateArgsLength
from nex.common.storage import StorageAPI

OnNewMatchAdded = RegisterAction("new_match_added", "match_id", "oracle_id", "match_details")
OnNewMatchConsensus = RegisterAction("new_match_consensus", "match_id", "oracle_id")
OnNewMatchConfirmed = RegisterAction("new_match_confirmed", "match_id", "oracle_id")

OnMatchOutcomeConsensus = RegisterAction("update_match_consensus", "match_id", "outcome", "oracle_id")
OnMatchOutcomeConfirmed = RegisterAction("update_match_confirmed", "match_id", "outcome", "oracle_id")

class Oracle():

    match_prefix = b'match/'
    oracle_prefix = b'oracle/'

    outcome_oracle_prefix = b'outcome_oracle/'
    outcome_count_prefix = b'outcome_count/'

    oracle_count_key = b'oracle/count'
    oracle_consensus_key = b'oracle/consensus'

    def AddMatch(self, args, oracleID):
        storage = StorageAPI()

        isValidSender = self.ValidateOracle(storage, oracleID)
        if isValidSender == False:
            return False

        isValidLength = ValidateArgsLength(args, 7)
        if isValidLength == False:
            return False

        matchID = CreateMatchID(args)

        matchKey = concat(self.match_prefix, matchID)
        match = storage.get(matchKey)

        if match == False:
            _ = StoreMatchDetails(storage, matchKey, args)

            match = "pending"

            OnNewMatchAdded(matchID, oracleID, args)
            
        if match == "pending":
            oracleKey = concat(matchKey, oracleID) 
            countKey = concat(matchKey, "/count")

            reachedConsensus = self.CheckMatchConsensus(storage, oracleKey, countKey)

            if reachedConsensus == False:
                OnNewMatchConsensus(matchID, oracleID)
            
            else: 
                storage.put(matchKey, "active")

                OnNewMatchConfirmed(matchID, oracleID)
                
            return  True
        else:
            msg1 = concat("Consensus has finished for: ", matchID)
            msg2 = concat(", Match state is currently: ", match)
            msg = concat(msg1, msg2)

            Log(msg)

        return False

    def UpdateMatchOutcome(self, args, oracleID):
        storage = StorageAPI()

        isValidSender = self.ValidateOracle(storage, oracleID)
        if isValidSender == False:
            return False

        isValidLength = ValidateArgsLength(args, 2)
        if isValidLength == False:
            return False    

        matchID = args[0]
        outcome = args[1]

        matchKey = concat(self.match_prefix, matchID)
        match = storage.get(matchKey)    

        if match != "active":
            msg1 = concat("Cannot update match: ", matchID)
            msg2 = concat(", Match state is currently: ", match)
            msg = concat(msg1, msg2)

            Log(msg)

            return False
        
        oracleSuffix = concat(self.outcome_oracle_prefix, oracleID)
        countSuffix = concat(self.outcome_count_prefix, outcome)

        oracleKey = concat(matchKey, oracleSuffix)   
        countKey = concat(matchKey, countSuffix)

        reachedConsensus = self.CheckMatchConsensus(storage, oracleKey, countKey)

        if reachedConsensus == False:
                OnMatchOutcomeConsensus(matchID, oracleID)
            
        else: 
            if outcome == "void":
                storage.put(matchKey, "void")

            else: 
                outcomeKey = concat(matchKey, "/outcome")

                storage.put(outcomeKey, outcome)
                storage.put(matchKey, "finished")


            OnMatchOutcomeConfirmed(matchID, outcome, oracleID)

        return True

    def ValidateOracle(self, storage:StorageAPI, oracleID):
        isOracle = CheckWitness(oracleID)
        if isOracle == False:
            msg = concat("Given address is not the sender: ", oracleID)
            Log(msg)
            return False

        return True

    def CheckMatchConsensus(self, storage:StorageAPI, oracleKey, countKey):
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


