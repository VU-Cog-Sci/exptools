from exptools.core.trial import MRITrial
from stim import BinocularDotStimulus, RandomBarFrameStimulus
import os
import exptools
import json
from psychopy import logging, visual, event
import numpy as np

class WaitTrial(MRITrial):

    def __init__(self, *args, **kwargs):
        super(WaitTrial, self).__init__(*args, **kwargs)
        self.ID = 'wait'

        self.text = visual.TextStim(self.screen, "Waiting for trigger", color='white', height=70)

    def draw(self):
        self.text.draw()
        super(WaitTrial, self).draw()

    def key_event(self, key):
        super(WaitTrial, self).key_event(key)

        if key == self.session.mri_trigger_key:
            self.stop()

        if key != self.session.mri_trigger_key:
            self.stop()
            self.session.stop()


class BinocularDotsTrial(MRITrial):

    def __init__(self, trial_idx, parameters, color='r', *args, **kwargs):
            
        phase_durations = [parameters['fixation_time'], parameters['stimulus_time']]

        super(BinocularDotsTrial, self).__init__(parameters=parameters,
                                                 phase_durations=phase_durations,
                                                 *args, 
                                                 **kwargs)
        self.ID = trial_idx
        self.color = color

        self.parameters['correct'] = None

        self.dot_stimulus = BinocularDotStimulus(screen=self.screen,
                                             trial=self,
                                             session=self.session,
                                             config=self.parameters,
                                             color=self.color,)

        size_fixation_pix = self.session.deg2pix(self.parameters['size_fixation_deg'])

        self.fixation = visual.GratingStim(self.screen, 
                                               tex='sin', 
                                               mask='circle', 
                                               size=size_fixation_pix, 
                                               texRes=512, 
                                               color='white', 
                                               sf=0)

        self.randombarstimulus = RandomBarFrameStimulus(screen=self.screen,
                                                        trial=self,
                                                        config=self.parameters,
                                                        session=self.session)


    def draw(self, *args, **kwargs):

        if self.phase == 0:
            self.fixation.draw()
            self.randombarstimulus.draw()
        elif self.phase == 1:    
            if self.parameters['draw_dots']:
                self.dot_stimulus.draw()

            self.fixation.draw()
            self.randombarstimulus.draw()

        super(BinocularDotsTrial, self).draw()


    def run(self):

        self.start_time = self.session.clock.getTime()
        
        while not self.stopped:
            
            # events and draw
            self.event()
            self.draw()

            if self.phase == 0:
                if self.session.clock.getTime() - self.start_time > self.phase_times[0]:
                    self.phase_forward()

            if self.phase == 1:
                if self.session.clock.getTime() - self.start_time > self.phase_times[1]:
                    self.phase_forward()
            
            if self.phase == 2:
                self.stopped = True

        
    
        self.stop()

    def stop(self):
        super(BinocularDotsTrial, self).stop()
        
        if self.color == 'r':
            self.session.parameters['red_intensity'] = self.dot_stimulus.element_master.color[0]
        elif self.color == 'b':
            self.session.parameters['blue_intensity'] = self.dot_stimulus.element_master.color[2]



    def key_event(self, key):

        if key in ['esc', 'escape', 'q']:
            self.events.append([-99,self.session.clock.getTime()-self.start_time])
            self.stopped = True
            self.session.stopped = True
            self.session.logging.info('run canceled by user')

        if key in ['a', 's']:

            if self.color == 'r':
                delta = np.array([0.025, 0, 0])
            elif self.color == 'b':
                delta = np.array([0, 0, 0.025])
            
            if key == 'a':
                self.dot_stimulus.element_master.color += delta
            else: 
                self.dot_stimulus.element_master.color -= delta

        if (key == self.parameters['left_key']) and not self.parameters['correct']:
            if self.parameters['direction'] == 180:
                self.parameters['correct'] = True
            else:
                self.parameters['correct'] = False

        if (key == self.parameters['right']) and not self.parameters['correct']:
            if self.parameters['direction'] == 0:
                self.parameters['correct'] = True
            else:
                self.parameters['correct'] = False


        super(BinocularDotsTrial, self).key_event(key)
