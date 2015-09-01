from os import environ
from twisted.internet.defer import inlineCallbacks

from autobahn.wamp.types import RegisterOptions, PublishOptions
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
import subprocess

IPTABLES = "iptables"
CHAIN_NAME = "PARENTAL_FORWARD"


def parse_iptables(options, insideMatch=False):
    """
    Parse arguments for iptables provided as a dictionary.

    The key-value pairs are morphed into arguments for iptables.  If the value
    is a dictionary, then it is assumed to be a (-m/--match) block.

    Example:
    options = {
        'd': '192.168.1.1',  # Becomes "-d 192.168.1.1"
        'time': {
            'timestart': '00:00',
            'timestop': '05:00'
        },  # Becomes "--match time --timestart 20:00 --timestop 04:00"
        'jump': 'DROP'  # Becomes "--jump DROP"
    }

    insideMatch: used by recursive call to signify that we have gone down a
    level and should not recurse.
    """
    parts = list()
    for key, value in options.items():
        if isinstance(value, dict):
            if insideMatch:
                print("Error in iptables rule specification: too many levels")
                return None

            parts.extend(["--match", key])
            parts.extend(parse_iptables(value, insideMatch=True))

        elif isinstance(value, list):
            if len(key) == 1:
                parts.append("-" + key)
            else:
                parts.append("--" + key)
            parts.extend(value)

        else:
            if len(key) == 1:
                parts.append("-" + key)
            else:
                parts.append("--" + key)
            parts.append(value)
    
    return parts


class Component(ApplicationSession):

    def testFunction(self):
        print 'Test fucntion called!'
        ruleDefs = [{
            'timestart': '13:00',
            'timestop': '05:00',
            'action': 'DROP'
        }] 

        self.setupForwardingTable(CHAIN_NAME)
        commands = self.getIptablesCommands(CHAIN_NAME, ruleDefs)
        self.executeCommands(commands)
        return 'Dropping Packets!'

    @inlineCallbacks
    def onJoin(self, details):
        print("session attached")

        yield self.register(self.testFunction, 'pd.nick.routerName.parentalControls')

        print("procedure registered")
  
    def setupForwardingTable(self, chain):

        print("setup")
        cmd = [IPTABLES, '--check', 'FORWARD', '--jump', chain]
        if subprocess.call(cmd) == 0:
            # Jump to chain already exists.
            cmd = [IPTABLES, '--flush', chain]
        else:
            # Jump rule did not exist, so chain probably does not either.
            cmd = [IPTABLES, '--new-chain', chain]
            subprocess.call(cmd)

            cmd = [IPTABLES, '--append', 'FORWARD', '--jump', chain]
            subprocess.call(cmd)

    def getIptablesCommands(self, chain, ruleDefs):
        """
        Generate iptables commands from rule definitions.
        ruleDefs should be a list of rule definitions.  Each rule definition should
        be a dictionary of iptables options, which will become one single iptables
        rule.
        Example (drop everything between midnight and 5am):
        ruleDefs = [{
            'time': {
                'timestart': '00:00',
                'timestop': '05:00'
            },
            'jump': 'DROP'
        }]
        """
        print("iptables")
        base_cmd = [IPTABLES, '--append', chain]

        commands = list()
        for rule in ruleDefs:
            cmd = list(base_cmd)
            cmd.extend(parse_iptables(rule))
            commands.append(cmd)

        return commands

    def executeCommands(self, commands):
        print("execute")
        for cmd in commands:
            subprocess.call(cmd)


if __name__ == '__main__':
    runner = ApplicationRunner(
        "ws://paradrop.io:9080/ws",
        u"crossbardemo",
        debug_wamp=False,  # optional; log many WAMP details
        debug=False,  # optional; log even more details
    )
    runner.run(Component)
