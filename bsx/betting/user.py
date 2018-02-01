from boa.blockchain.vm.Neo.Blockchain import GetHeight
from boa.blockchain.vm.Neo.Action import RegisterAction
from boa.blockchain.vm.Neo.Runtime import Notify,CheckWitness,Log
from boa.code.builtins import concat, sha1
from bsx.common.utils import ValidateArgsLength, GetCurrentTimestamp
from nex.common.storage import StorageAPI
from nex.common.txio import Attachments,get_asset_attachments

class User():

    isUser = 0

    balance = 0
    
    balanceKey = 0

    balancePrefix = b'balance/'

    def AddToBalance(self, storage:StorageAPI, amount):
        newBalance = self.balance + amount
        storage.put(self.balanceKey, newBalance)

        return

    def RemoveFromBalance(self, storage:StorageAPI, amount):
        newBalance = self.balance - amount          # We validate A - B before here
        storage.put(self.balanceKey, newBalance)

        return

    def GetBalance(self, args, userID):
        storage = StorageAPI()

        isValidLength = ValidateArgsLength(args, 1)
        if isValidLength == False:
            return False

        userID = args[0]

        balanceKey = concat(self.balancePrefix, userID)
        balance = storage.get(balanceKey)

        return balance


def GetUser(storage:StorageAPI, sender, validateUser) -> User:
    user = User()

    # Failing CheckWitness throws some warnings that clog up the log
    # This just allows us to skip it when we know it will fail
    if validateUser:
        isSender = CheckWitness(sender)
        if isSender == False:   # isSender doesn't like being evaluated as True here hence the work around
            _ = 1                     
        else:
            _ = 1               # breaks without this as well   
            user.isUser = True
            
    balanceKey = concat(user.balancePrefix, sender)
    balance = storage.get(balanceKey)

    user.balance = 1000000000
    user.balanceKey = balanceKey

    return user

def DepositFunds():
    storage = StorageAPI()

    attachments = get_asset_attachments()
    gasAttached = attachments.gas_attached      # Need to manually store or methods break later on
    userID = attachments.sender_addr

    if gasAttached == 0:
        Log("No GAS has been attached")
        return False
    
    user = GetUser(storage, userID, False)

    _ = user.AddToBalance(storage, gasAttached)

    return True