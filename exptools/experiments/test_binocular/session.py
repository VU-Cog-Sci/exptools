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
        self.pausing = True

        if 'tr' not in kwargs:
            self.tr = config['tr']
        if 'simulate_mri_trigger' not in kwargs:
            self.simulate_mri_trigger = config['simulate_mri_trigger']

        self.staircase = ThreeUpOneDownStaircase(0.5, 0.01)


    def run(self):
        """docstring for fname"""
        # cycle through trials

        trial_idx = 0


        block_length = self.parameters['block_length']
        rest_length = self.parameters['rest_length']
        total_length = block_length + rest_length

        while not self.stopped:

            if self.pausing:
                wait_trial = WaitTrial(session=self)
                wait_trial.run()


            color_idx = int(((self.current_tr-1) * self.tr)  / total_length) % 2
            self.parameters['color'] = ['r', 'b'][color_idx]

            show_dots = ((self.current_tr-1) * self.tr)  % total_length < block_length
            self.parameters['draw_dots'] = show_dots

            # Randomly sample direction
            direction = np.random.choice([180, 0])
            self.parameters['direction'] = direction

            # Set coherence
            self.parameters['coherence'] = self.staircase.get_intensity()

            # Construct trial
            trial = BinocularDotsTrial(trial_idx, 
                                       parameters=self.parameters.copy(),
                                       screen=self.screen, 
                                       session=self, )


            logging.info('Running trial %d' % trial_idx)
            trial.run()

            if trial.parameters['correct'] is not None:
                logging.critical('Sending answer to staircase: %s' % trial.parameters['correct'])
                self.staircase.answer(trial.parameters['correct'])
                logging.critical('Current coherence: %.2f' % self.staircase.get_intensity())


            trial_idx += 1

        self.close()
