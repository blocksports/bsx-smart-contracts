from boa.blockchain.vm.Neo.Blockchain import GetHeight
from boa.blockchain.vm.Neo.Action import RegisterAction
from boa.blockchain.vm.Neo.Runtime import Notify,CheckWitness
from boa.code.builtins import concat, sha1
from bsx.common.utils import ValidateArgsLength, GetCurrentTimestamp
from nex.common.storage import StorageAPI

OnOracleAdded = RegisterAction("oracle_added", "oracle_id", "oracle_count")
OnOracleRemoved = RegisterAction("oracle_removed", "oracle_id")

class Admin():

    OWNER = b'#\xba\'\x03\xc52c\xe8\xd6\xe5"\xdc2 39\xdc\xd8\xee\xe9'

    oracle_prefix = b'oracle/'

    oracle_count_key = b'oracle/count'
    oracle_consensus_key = b'oracle/consensus'
    
    admin_init_key = b'admin/initialised'

    def AddOracle(self, args):
        storage = StorageAPI()

        isValidOwner = self.ValidateOwner()
        if isValidOwner == False:
            return False

        isValidLength = ValidateArgsLength(args, 1)
        if isValidLength == False:
            return False    

        oracleID = args[0]
        oracleKey = concat(self.oracle_prefix, oracleID)

        isOracle = storage.get(oracleKey)
        if isOracle == True:
            Log("Address is already an oracle")
            return False

        oracleCount = storage.get(self.oracle_count_key)
        newCount = oracleCount + 1

        storage.put(oracleKey, True)
        storage.put(self.oracle_count_key, newCount)

        OnOracleAdded(oracleID, newCount)

        return True

    def RemoveOracle(self, args):
        storage = StorageAPI()

        isValidOwner = self.ValidateOwner()
        if isValidOwner == False:
            return False

        isValidLength = ValidateArgsLength(args, 1)
        if isValidLength == False:
            return False    

        oracleID = args[0]
        oracleKey = concat(self.oracle_prefix, oracleID)

        isOracle = storage.get(oracleKey)
        if isOracle == True:
            Log("Address is already an oracle")
            return False     

        return True  

    def InitialiseContract(self):
        storage = StorageAPI()

        isValidOwner = self.ValidateOwner()
        if isValidOwner == False:
            return False
        
        isInitialised = storage.get(self.admin_init_key)
        if isInitialised:
            Log("Contract has already been initialised")
            return False

        oracleKey = concat(self.oracle_prefix, self.OWNER)

        storage.put(oracleKey, True)
        storage.put(self.oracle_count_key, 1)
        storage.put(self.oracle_consensus_key, 70)
        storage.put(self.admin_init_key, True)

        return True

    def ValidateOwner(self):
        isOwner = CheckWitness(self.OWNER)
        if isOwner == False:
            Log("Sender is not the owner")
            return False

        return True