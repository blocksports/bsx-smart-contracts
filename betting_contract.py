"""
Block Sports Betting Contract

author: Mirren King-Smith
version: 0.1.0

"""

from boa.blockchain.vm.Neo.Transaction import *
from boa.blockchain.vm.Neo.Header import GetTimestamp,GetNextConsensus
from boa.blockchain.vm.Neo.Blockchain import GetHeader,GetHeight
from boa.blockchain.vm.Neo.Runtime import GetTrigger
from boa.blockchain.vm.Neo.TriggerType import Application,Verification
from bsx.betting.user import User, DepositFunds, GetUser
from bsx.betting.exchange import Exchange
from bsx.betting.admin import Admin

def Main(operation, args, sender=None):

    trigger = GetTrigger()

    if trigger == Application():

        exchange = Exchange()

        """
            Standard Operations

            No Permissions Required
        """

        if operation == "depositFunds":
            return DepositFunds()

        elif operation == "distributeBetWinnings":
            return exchange.DistributeBetWinnings(args)

        elif operation == "processBetQueue":
            return exchange.ProcessBetQueue(args)

        """
            User Operations

            Requires Sender to be the User 
        """

        if operation == "placeBet":
            return exchange.PlaceBet(args, sender)

        elif operation == "cancelBet":
            return exchange.CancelBet(args, sender)

        """ 
            Admin Operations

            Requires Owner Permissions
        """

        admin = Admin()

        if operation == 'killAdmin':
            return False

        elif operation == 'initContract':
            return admin.InitialiseContract()

    return False