from boa.blockchain.vm.Neo.Blockchain import GetHeight
from boa.blockchain.vm.Neo.Action import RegisterAction
from boa.blockchain.vm.Neo.Runtime import GetTrigger,CheckWitness,Notify,Log
from boa.code.builtins import concat
from nex.common.storage import StorageAPI

def ValidateArgsLength(args, length_required):
    length = len(args)

    if length != length_required:

        msg_a = concat("Expected length: ", length_required)
        msg_b = concat(", Received length: ", length) 
        msg = concat(msg_a, msg_b)
        Log(msg)

        return False

    return True

def GetCurrentTimestamp():
    blockHeight = GetHeight()
    blockHeader = GetHeader(blockHeight)
    return blockHeader.Timestamp    