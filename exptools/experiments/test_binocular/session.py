from exptools.core import Session, MRISession
from trial import BinocularDotsTrial, WaitTrial
from psychopy import clock
import os
import exptools
import json
from exptools.core.staircase import ThreeUpOneDownStaircase 

from psychopy import logging
import numpy as np
logging.console.setLevel(logging.CRITICAL)

class BinocularSession(MRISession):


    def __init__(self, *args, **kwargs):

        super(BinocularSession, self).__init__(*args, **kwargs)

        self.create_screen(full_screen=True, engine='psychopy')

        # Set up parameters
        config_file = os.path.join(exptools.__path__[0], 'experiments',
                              'test_binocular', 'default_settings.json')

        with open(config_file) as config_file:
            config = json.load(config_file)
        
        self.parameters = config
        self.stopped = False

        if 'tr' not in kwargs:
            self.tr = config['tr']
        if 'simulate_mri_trigger' not in kwargs:
            self.simulate_mri_trigger = config['simulate_mri_trigger']

        self.staircase = ThreeUpOneDownStaircase(0.5, 0.01, increment_value=0.01)


    def run(self):
        """docstring for fname"""
        # cycle through trials

        trial_idx = 0

        wait_trial = WaitTrial(session=self)
        wait_trial.run()

        block_length = self.parameters['block_length']
        rest_length = self.parameters['rest_length']
        total_length = block_length + rest_length

        while not self.stopped:
            color_idx = int(((self.current_tr-1) * self.tr)  / total_length) % 2
            color = ['r', 'b'][color_idx]

            show_dots = ((self.current_tr-1) * self.tr)  % total_length < block_length
            self.parameters['draw_dots'] = show_dots

            # Randomly sample direction
            direction = np.random.choice([180, 0])
            self.parameters['direction'] = direction

            trial = BinocularDotsTrial(trial_idx, 
                                       parameters=self.parameters.copy(),
                                       screen=self.screen, 
                                       session=self, 
                                       color=color)
            logging.info('Running trial %d' % trial_idx)
            trial.run()
            trial_idx += 1

        self.close()
