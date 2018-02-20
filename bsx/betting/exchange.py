from boa.blockchain.vm.Neo.App import RegisterAppCall
from boa.blockchain.vm.Neo.Blockchain import GetHeight
from boa.blockchain.vm.Neo.Action import RegisterAction
from boa.blockchain.vm.Neo.Runtime import Notify,CheckWitness
from boa.code.builtins import concat, sha1
from bsx.betting.bet import Bet, InitialiseBet, InitialiseNewBet
from bsx.betting.user import User, GetUser
from bsx.betting.queue import Queue, InitialiseQueue
from bsx.common.utils import ValidateArgsLength, GetCurrentTimestamp
from nex.common.storage import StorageAPI

InvokeMatchContract = RegisterAppCall("d21bee8a53177becfbf417cef93ec1e5aee1033a", "operation", "args", "sender")

OnBetAdded = RegisterAction("bet_added", "bet_id", "user_id", "bet_details", "bet_index")

OnBetCancelled = RegisterAction("bet_cancelled", "bet_id", "user_id", "bet_details")

OnVoidBetClaimed = RegisterAction("void_bet_claimed", "bet_id", "user_id", "bet_details")

OnBetClaimed = RegisterAction("bet_claimed", "bet_id" "user_id", "bet_details")

class Exchange():

    minimumBet = 10000000

    minimumOdds = 101

    feePoolID = b'fee_pool'

    def PlaceBet(self, args, sender):
        storage = StorageAPI()

        user = GetUser(storage, sender, True)
        if user.isUser == False:
            return False
        
        isValidLength = ValidateArgsLength(args, 5)
        if isValidLength == False:
            return False

        isValidBet = self.ValidateNewBet(user, args)
        if isValidBet == False:
            return False
        
        bet = InitialiseNewBet(storage, args)

        user.RemoveFromBalance(storage, bet.betAmount)

        storage.put(bet.betAmountKey, bet.betAmount)
        storage.put(bet.unmatchedAmountKey, bet.returnAmount)
        storage.put(bet.betMakerKey, sender)
        storage.put(bet.statusKey, "valid")

        OnBetAdded(bet.betID, sender, args, bet.betIndex)

        return True

    def CancelBet(self, args, sender):
        storage = StorageAPI()

        user = GetUser(storage, sender, True)
        if user.isUser == False:
            return False
        
        isValidLength = ValidateArgsLength(args, 5)
        if isValidLength == False:
            return False

        bet = InitialiseBet(storage, args)
        
        isValidCancel = self.ValidateCancelBet(bet, sender)
        if isValidCancel == False:
            return False

        storage.put(bet.statusKey, "cancelled")
        _ = user.AddToBalance(storage, bet.betAmount)

        OnBetCancelled(bet.betID, sender, args)
        
        return True
    
    def ProcessBetQueue(self, args):
        storage = StorageAPI()
        
        isValidLength = ValidateArgsLength(args, 4)
        if isValidLength == False:
            return False    
        
        queue = InitialiseQueue(storage, args)

        if queue.betStatus == "cancelled":
            Log("Bet has been cancelled, move to next bet")

            newQueueIndex = queue.index + 1
            storage.put(queue.indexKey, newQueueIndex) 

            return True                                     # could evaluate more, but leave here for v0.1

        elif queue.betStatus != "valid":
            Log("Bet queue contains no bets to be matched")

            return False
        
        return queue.ProcessLoop(storage)

    def DistributeBetWinnings(self, args):
        storage = StorageAPI()

        isValidLength = ValidateArgsLength(args, 5)
        if isValidLength == False:
            return False

        bet = InitialiseBet(storage, args)

        outcome = self.ValidateDistributeWinnings(bet)
        if outcome == False:
            return False
        
        userID = bet.betMaker                               # breaks if you pass this in directly
        user = GetUser(storage, userID, False)

        storage.put(bet.statusKey, "claimed")

        if outcome == "void":
            """ Reimburse original bet if the match was voided """

            _ = user.AddToBalance(storage, bet.betAmount)

            _ = OnVoidBetClaimed(bet.betID, bet.betMaker, args)
            
        else:
            bet = bet.CalculateWinnings()

            feePoolKey = self.feePoolID                     # breaks if you pass this in directly
            feePool = GetUser(storage, feePoolKey, False)

            _ = user.AddToBalance(storage, bet.returnAmount)
            _ = feePool.AddToBalance(storage, bet.feeAmount)

            _ = OnBetClaimed(bet.betID, bet.betMaker, args)

        return True  

    def ValidateNewBet(self, user:User, args):
        matchID = args[0]
        odds = args[2]
        betType = args[3]
        betAmount = args[4]

        if betAmount > user.balance:
            msg = concat("Insufficient funds for bet, balance is: ", user.balance)
            Log(msg)
            return False
        
        if betAmount < self.minimumBet:
            msg = concat("Bet must be equal to or larger than: ", self.minimumBet)
            Log(msg)
            return False

        if odds < self.minimumOdds:
            msg = concat("Odds must be equal to or larger than: ", self.minimumOdds)
            Log(msg)
            return False 

        if betType != "back" and betType != "lay":
            msg = concat("Bet type must be either back or lay, type given: ", betType)
            Log(msg)
            return False
        
        invokeArgs = [ matchID ]

        isValidMatch = InvokeMatchContract("validateActiveMatch", invokeArgs, 0)
        
        return isValidMatch
    
    def ValidateCancelBet(self, bet:Bet, sender):
        if bet.status != "valid":
            msg = concat("Cannot cancel bet with status: ", bet.status)
            Log(msg)
            return False  

        if bet.betMaker != sender:
            Log("Cannot cancel someone elses bet")
            return False            

        bet = bet.CalculateReturnAmount()

        if bet.returnAmount != bet.unmatchedAmount:
            Log("Bet has been matched or partially matched and cannot be cancelled")
            return False

        return True
    
    def ValidateDistributeWinnings(self, bet:Bet):
        if bet.status != "valid":
            msg = concat("Cannot distribute bet winnings with status: ", bet.status)
            Log(msg)
            return False  

        invokeArgs = [ bet.matchID ]

        matchOutcome = InvokeMatchContract("checkMatchOutcome", invokeArgs, 0)
        if matchOutcome == False:
            return False
        
        elif (bet.betType == "back" and matchOutcome != bet.outcome) and (bet.betType == "lay" and matchOutcome == bet.outcome) and matchOutcome != "void": 
            msg = concat("Incorrect bet outcome, winning outcome was: ", matchOutcome)
            Log(msg)
            return False

        return matchOutcome