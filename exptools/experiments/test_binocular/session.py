from exptools.core import Session, MRISession
from trial import BinocularDotsTrial
from psychopy import clock
import os
import exptools
import json

from psychopy import logging
logging.console.setLevel(logging.INFO)

class BinocularSession(MRISession):


    def __init__(self, *args, **kwargs):

        super(BinocularSession, self).__init__(*args, **kwargs)

        self.create_screen(full_screen=True, engine='psychopy')

        config_file = os.path.join(exptools.__path__[0], 'experiments',
                              'test_binocular', 'default_settings.json')

        with open(config_file) as config_file:
            config = json.load(config_file)
        
        self.parameters = config
        self.stopped = False

        self.tr = config['tr']
        self.simulate_mri_trigger = config['simulate_mri_trigger']


    def run(self):
        """docstring for fname"""
        # cycle through trials

        trial_idx = 0

        while not self.stopped:

            color = ['r', 'b'][trial_idx % 2]
            trial = BinocularDotsTrial(trial_idx, 
                                       parameters=self.parameters.copy(),
                                       screen=self.screen, 
                                       session=self, 
                                       color=color)
            logging.info('Running trial %d' % trial_idx)
            trial.run()
            trial_idx += 1

        self.close()
