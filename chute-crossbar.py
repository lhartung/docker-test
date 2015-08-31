from os import environ
from twisted.internet.defer import inlineCallbacks

from autobahn.wamp.types import RegisterOptions, PublishOptions
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
import subprocess

IPTABLES = "iptables"
CHAIN_NAME = "PARENTAL_FORWARD"

iptables_options = {
    'destination': '--destination {}',
    'mac': '--match mac --mac-source {}',
    'timestart': '--match time --timestart {}',
    'timestop': '--match time --timestop {}',
    'days': '--match time --weekday {}',
    'action': '--jump {}'
}


class Component(ApplicationSession):

    def testFunction(self):
        print 'Test fucntion called!'
        ruleDefs = [{
            'timestart': '13:00',
            'timestop': '05:00',
            'action': 'DROP'
        }] 

        setupForwardingTable(CHAIN_NAME)
        commands = getIptablesCommands(CHAIN_NAME, ruleDefs)
        executeCommands(commands)
        return 'Dropping Packets!'

    def setupForwardingTable(chain):
        cmd = [IPTABLES, '--check', 'forward', '--jump', chain]
        if subprocess.call(cmd) == 0:
            # Jump to chain already exists.
            cmd = [IPTABLES, '--flush', chain]
        else:
            # Jump rule did not exist, so chain probably does not either.
            cmd = [IPTABLES, '--new-chain', chain]
            subprocess.call(cmd)

            cmd = [IPTABLES, '--append', 'forward', '--jump', chain]
            subprocess.call(cmd)

    def getIptablesCommands(chain, ruleDefs):
        """
        Generate iptables commands from rule definitions.
        ruleDefs should be a list of rule definitions.  Each rule definition should
        be a dictionary of iptables options, which will become one single iptables
        rule.
        Example (drop everything between midnight and 5am):
        ruleDefs = [{
            'timestart': '00:00',
            'timestop': '05:00',
            'action': 'DROP'
        }]
        """
        base_cmd = [IPTABLES, '--append', chain]

        commands = list()
        for rule in ruleDefs:
            cmd = list(base_cmd)
            for key, value in rule.items():
                if key in iptables_options:
                    option = iptables_options[key].format(value)
                    cmd.extend(option.split())
            commands.append(cmd)

        return commands

    def executeCommands(commands):
        for cmd in commands:
            subprocess.call(cmd)

        @inlineCallbacks
        def onJoin(self, details):
            print("session attached")

            yield self.register(self.testFunction, 'pd.nick.routerName.parentalControls')

            print("procedure registered")


if __name__ == '__main__':
    runner = ApplicationRunner(
        "ws://paradrop.io:9080/ws",
        u"crossbardemo",
        debug_wamp=False,  # optional; log many WAMP details
        debug=False,  # optional; log even more details
    )
    runner.run(Component)
