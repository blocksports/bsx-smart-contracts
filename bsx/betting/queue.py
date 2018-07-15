from boa.blockchain.vm.Neo.Blockchain import GetHeight
from boa.code.builtins import concat, sha1
from nex.common.storage import StorageAPI

class Queue():

    rawQueueID = 0
    rawCounterQueueID = 0

    queueKey = 0
    counterQueueKey = 0

    indexKey = 0
    counterIndexKey = 0

    index = 0

    betID = 0
    betStatus = 0

    exitLoop = 0

    def CreateQueueIDs(self, args):
        eventID = args[0]
        outcome = args[1]
        odds = args[2]
        betType = args[3]

        rawQueue = concat(eventID, outcome)
        rawQueue = concat(rawQueue, odds)

        rawBackID = concat(rawQueue, "back")
        rawLayID = concat(rawQueue, "lay")
        backID = sha1(rawBackID)
        layID = sha1(rawLayID)

        if betType == "back":
            self.rawQueueID = rawBackID
            self.rawCounterQueueID = rawLayID
            self.queueKey = concat("bet_queue/", backID)
            self.counterQueueKey = concat("bet_queue/", layID)

        elif betType == "lay":
            self.rawQueueID = rawLayID
            self.rawCounterQueueID = rawBackID
            self.queueKey = concat("bet_queue/", layID)
            self.counterQueueKey = concat("bet_queue/", backID)

        self.indexKey = concat(self.queueKey, "/index")
        self.counterIndexKey = concat(self.counterQueueKey, "/index")

        return self

    def ProcessLoop(self, storage:StorageAPI):
        unmatchedAmountKey = concat("bet/unmatched", self.betID)
        unmatchedAmount = storage.get(unmatchedAmountKey)

        counterIndex = storage.get(self.counterIndexKey)
        if counterIndex == 0:
            # Indexing starts at 1
            counterIndex = 1

        oldUnmatchedAmount = unmatchedAmount
        oldIndex = self.index
        oldCounterIndex = counterIndex

        betLoop = [1, 2, 3, 4] # Can't store arrays as class field
        
        """ Loops until bet is completely matched or GAS is exhausted (4 loops)"""
        for i in betLoop:

            if self.exitLoop == 1:
                continue            # break creates infinite loop? so we continue here instead

            rawCounterBetID = concat(self.rawCounterQueueID, counterIndex)
            counterBetID = sha1(rawCounterBetID)

            counterBetStatusKey = concat("bet/status/", counterBetID)
            counterBetStatus = storage.get(counterBetStatusKey)

            if counterBetStatus == "cancelled":
                Log("Counter bet has been cancelled, will move to next counter bet")

                counterIndex = counterIndex + 1

                if i == 4:
                    self.exitLoop = 1

            elif counterBetStatus != "valid":
                Log("Counter bet queue contains no bets to be matched")
                self.exitLoop = 1

            else:
                counterUnmatchedAmountKey = concat("bet/unmatched/", counterBetID)
                counterUnmatchedAmount = storage.get(counterUnmatchedAmountKey)

                if unmatchedAmount > counterUnmatchedAmount:
                    """ Counter bet has been matched """

                    unmatchedAmount = unmatchedAmount - counterUnmatchedAmount
                    counterUnmatchedAmount = 0

                    storage.put(counterUnmatchedAmountKey, counterUnmatchedAmount)

                    counterQueueIndex = counterQueueIndex + 1

                    if i == 4:
                        self.exitLoop = 1

                elif unmatchedAmount == counterUnmatchedAmount:
                    """ Both sides have been matched"""

                    unmatchedAmount = 0
                    counterUnmatchedAmount = 0

                    storage.put(counterUnmatchedAmountKey, counterUnmatchedAmount)

                    counterQueueIndex = counterQueueIndex + 1
                    self.index = self.index + 1

                    self.exitLoop = 1

                else:
                    """" Bet has been matched """

                    unmatchedAmount = 0
                    counterUnmatchedAmount = counterUnmatchedAmount - unmatchedAmount

                    storage.put(counterUnmatchedAmountKey, counterUnmatchedAmount)

                    self.index = self.index + 1

                    self.exitLoop = 1

        """ If the bet has been matched at all, store new unmatched amount """
        if unmatchedAmount < oldUnmatchedAmount:
            storage.put(unmatchedAmountKey, unmatchedAmount)

        """ If the bet has been completely matched, store the new bet queue index """
        if self.index > oldIndex:
            storage.put(self.indexKey, self.index)

        """ If any of the counter bets have been matched, store the new counter bet queue index """
        if counterIndex > oldCounterIndex:
            storage.put(self.counterIndexKey, counterIndex)    
        
        return True

def InitialiseQueue(storage:StorageAPI, args) -> Queue:
    queue = Queue()

    queue = queue.CreateQueueIDs(args) 

    queue.index = storage.get(queue.indexKey)
    if queue.index == 0:
        # Indexing starts at 1
        queue.index = 1

    rawBetID = concat(queue.rawQueueID, queue.index)
    queue.betID = sha1(rawBetID)

    betStatusKey = concat("bet/status/", queue.betID)
    queue.betStatus = storage.get(betStatusKey)
    
    return queue