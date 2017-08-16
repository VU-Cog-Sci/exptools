from exptools.core import Session
from trial import BinocularDotsTrial
from psychopy import clock

class BinocularSession(Session):


    def __init__(self, *args, **kwargs):
        super(BinocularSession, self).__init__(*args, **kwargs)
        self.create_screen(full_screen=False, engine='psychopy')

    def run(self):
        """docstring for fname"""
        # cycle through trials

        trial = 1 
        
        trial = BinocularDotsTrial(screen=self.screen, session=self)
        
        for i in xrange(1000):
            trial.draw()
            clock.wait(0.01)

        self.close()
