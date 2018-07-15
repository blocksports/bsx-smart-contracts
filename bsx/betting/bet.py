from boa.blockchain.vm.Neo.Blockchain import GetHeight
from boa.code.builtins import concat, sha1
from nex.common.storage import StorageAPI

class Bet():

    betID = 0

    eventID = 0
    outcome = 0
    odds = 0
    betType = 0
    betIndex = 0

    betAmount = 0
    unmatchedAmount = 0
    betMaker = 0
    status = 0

    returnAmount = 0
    feeAmount = 0

    betAmountKey = 0
    unmatchedAmountKey = 0
    betMakerKey = 0
    statusKey = 0

    feePercent = 200        
    feeFactor = 10000

    oddsFactor = 100

    def CreateBetID(self):
        rawBetID = concat(self.eventID, self.outcome)
        rawBetID = concat(rawBetID, self.odds)
        rawBetID = concat(rawBetID, self.betType)
        rawBetID = concat(rawBetID, self.betIndex)  

        self.betID = sha1(rawBetID)

        return self    

    def CreateNewBetID(self, storage:StorageAPI):
        rawQueueID = concat(self.eventID, self.outcome)
        rawQueueID = concat(rawQueueID, self.odds)    
        rawQueueID = concat(rawQueueID, self.betType)

        queueID = sha1(rawQueueID)

        betQueuePrefix = concat("bet_queue/", queueID)
        betQueueLengthKey = concat(betQueuePrefix, "/length")

        queueLength = storage.get(betQueueLengthKey)
        newQueueLength = queueLength + 1

        storage.put(betQueueLengthKey, newQueueLength)

        rawBetID = concat(rawQueueID, newQueueLength)

        self.betID = sha1(rawBetID)
        self.betIndex = newQueueLength

        return self                        
        
    def CalculateReturnAmount(self):
        if self.betType == "back":
            self.returnAmount = (self.betAmount * self.odds - self.betAmount * self.oddsFactor) / self.oddsFactor
        else:
            self.returnAmount = (self.betAmount * self.oddsFactor) / (self.odds - self.oddsFactor)

        return self

    def CalculateWinnings(self):
        _ = self.CalculateReturnAmount()

        adjustedReturn = self.returnAmount - self.unmatchedAmount

        self.feeAmount = (adjustedReturn * self.feePercent) / self.feeFactor
        self.returnAmount = self.betAmount + adjustedReturn + self.feeAmount

        return self

def InitialiseBet(storage:StorageAPI, args) -> Bet:
    bet = Bet()

    bet.eventID = args[0]
    bet.outcome = args[1]
    bet.odds = args[2]
    bet.betType = args[3]
    bet.betIndex = args[4]

    bet = bet.CreateBetID()

    bet.betAmountKey = concat("bet/amount/", bet.betID) 
    bet.unmatchedAmountKey = concat("bet/unmatched/", bet.betID) 
    bet.betMakerKey = concat("bet/maker/", bet.betID) 
    bet.statusKey = concat("bet/status/", bet.betID) 

    bet.betAmount = storage.get(bet.betAmountKey)
    bet.unmatchedAmount = storage.get(bet.unmatchedAmountKey)
    bet.betMaker = storage.get(bet.betMakerKey)
    bet.status = storage.get(bet.statusKey)

    return bet

def InitialiseNewBet(storage:StorageAPI, args) -> Bet:
    bet = Bet()

    bet.eventID = args[0]
    bet.outcome = args[1]
    bet.odds = args[2]
    bet.betType = args[3]
    bet.betAmount = args[4]

    bet = bet.CreateNewBetID(storage)
    bet = bet.CalculateReturnAmount()

    bet.betAmountKey = concat("bet/amount/", bet.betID) 
    bet.unmatchedAmountKey = concat("bet/unmatched/", bet.betID) 
    bet.betMakerKey = concat("bet/maker/", bet.betID) 
    bet.statusKey = concat("bet/status/", bet.betID) 

    return bet
