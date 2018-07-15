"""
Block Sports event Contract

author: Mirren King-Smith
version: 0.1.0

"""

from boa.blockchain.vm.Neo.Transaction import *
from boa.blockchain.vm.Neo.Blockchain import GetHeader,GetHeight
from boa.blockchain.vm.Neo.Header import GetTimestamp,GetNextConsensus
from boa.blockchain.vm.Neo.Runtime import GetTrigger,CheckWitness,Notify,Log
from boa.blockchain.vm.Neo.TriggerType import Application,Verification
from bsx.events.oracle import Oracle
from bsx.events.event import Event
from bsx.events.admin import Admin
from nex.common.storage import StorageAPI

def Main(operation, args, sender=None):

    trigger = GetTrigger()

    if trigger == Application():
        
        context = GetContext()

        """
            Standard Operations

            No Permissions Required
        """

        event = Event()

        if operation == 'validateActiveEvent':
            return event.ValidateActiveEvent(args)

        elif operation == 'checkEventOutcome':
            return event.CheckEventOutcome(args)

        """
            Oracle Operations

            Requires Oracle Permissions 
        """

        oracle = Oracle()

        if operation == "addEvent":
            return oracle.AddEvent(args, sender)

        elif operation == "updateEventOutcome":
            return oracle.UpdateEventOutcome(args, sender)

        elif operation == "deleteSelf":
            return True

        """
            Admin Operations

            Requires Owner Permissions
        """

        admin = Admin()

        if operation == 'addOracle':
            return admin.AddOracle(args)

        elif operation == 'removeOracle':
            return admin.RemoveOracle(args)

        elif operation == 'killAdmin':
            return True

        elif operation == 'initContract':
            return admin.InitialiseContract()

    elif trigger == Verification():
        admin = Admin()

        return admin.ValidateOwner()

    return False
