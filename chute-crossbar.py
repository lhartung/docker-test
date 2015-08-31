from os import environ
from twisted.internet.defer import inlineCallbacks

from autobahn.wamp.types import RegisterOptions, PublishOptions
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner


class Component(ApplicationSession):

    def testFunction(self):
        print 'Test fucntion called!'
        return 'Holy Shit!'

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
