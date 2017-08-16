from exptools.core.trial import Trial
from stim import BinocularDotStimulus

class BinocularDotsTrial(Trial):

    def __init__(self, stimulus_config_file=None, *args, **kwargs):
            
        super(BinocularDotsTrial, self).__init__(*args, **kwargs)

        self.stimulus = BinocularDotStimulus(screen=self.screen,
                                             trial=self,
                                             config_file=stimulus_config_file,
                                             session=self.session)

    def draw(self, *args, **kwargs):

        self.stimulus.draw()

        super(BinocularDotsTrial, self).draw( )
