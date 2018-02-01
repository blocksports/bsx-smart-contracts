from boa.blockchain.vm.Neo.Blockchain import GetHeight
from boa.blockchain.vm.Neo.Action import RegisterAction
from boa.blockchain.vm.Neo.Runtime import Notify,CheckWitness
from boa.code.builtins import concat, sha1
from bsx.common.utils import ValidateArgsLength, GetCurrentTimestamp
from nex.common.storage import StorageAPI

class Admin():

    OWNER = b'#\xba\'\x03\xc52c\xe8\xd6\xe5"\xdc2 39\xdc\xd8\xee\xe9'
    
    admin_init_key = b'admin/initialised'

    def InitialiseContract(self):
        storage = StorageAPI()

        isValidOwner = self.ValidateOwner()
        if isValidOwner == False:
            return False
        
        isInitialised = storage.get(self.admin_init_key)
        if isInitialised:
            Log("Contract has already been initialised")
            return False

        storage.put(self.admin_init_key, True)

        return True

    def ValidateOwner(self):
        isOwner = CheckWitness(self.OWNER)
        if isOwner == False:
            Log("Sender is not the owner")
            return False

        return True