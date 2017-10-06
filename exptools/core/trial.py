import numpy as np
from .session import MRISession
from psychopy import logging, event

class Trial(object):
    def __init__(self, parameters = {}, phase_durations = [], session = None, screen = None, tracker = None):

        self.parameters = parameters.copy()
        self.phase_durations = phase_durations

        self.tracker = tracker
        self.session = session

        if screen is None:
            self.screen = self.session.screen
        else:
            self.screen = screen

        self.events = []
        self.phase = 0
        self.phase_times = np.cumsum(np.array(self.phase_durations))
        self.stopped = False

    def create_stimuli(self):
        pass

    def run(self):
        self.start_time = self.session.clock.getTime()
        if self.tracker:
            self.tracker.log('trial ' + str(self.ID) + ' started at ' + str(self.start_time) )
            self.tracker.send_command('record_status_message "Trial ' + str(self.ID) + '"')
        self.events.append('trial ' + str(self.ID) + ' started at ' + str(self.start_time))

        while not self.stopped:
            self.draw()
            self.event()


    def stop(self):
        self.stop_time = self.session.clock.getTime()
        self.stopped = True
        if self.tracker:
            # pipe parameters to the eyelink data file in a for loop so as to limit the risk of flooding the buffer
            for k in self.parameters.keys():
                self.tracker.log('trial ' + str(self.ID) + ' parameter\t' + k + ' : ' + str(self.parameters[k]) )
                time_module.sleep(0.0005)
            self.tracker.log('trial ' + str(self.ID) + ' stopped at ' + str(self.stop_time) )
        self.session.outputDict['eventArray'].append(self.events)
        self.session.outputDict['parameterArray'].append(self.parameters)

    def key_event(self, key):
        if self.tracker:
            self.tracker.log('trial ' + str(self.ID) + ' event ' + str(key) + ' at ' + str(self.session.clock.getTime()) )
        self.events.append('trial ' + str(self.ID) + ' event ' + str(key) + ' at ' + str(self.session.clock.getTime()))


    def feedback(self, answer, setting):
        """feedback give the subject feedback on performance"""
        if setting != 0.0:
            if cmp(setting, 0) == answer:
                self.session.play_sound( sound_index = 0 )
            else:
                self.session.play_sound( sound_index = 1 )

    def draw(self):
        """draw function of the Trial superclass finishes drawing by clearing, drawing the viewport and swapping buffers"""
        self.screen.flip()

    def phase_forward(self):
        """go one phase forward"""
        self.phase += 1
        phase_time = str(self.session.clock.getTime())
        self.events.append('trial ' + str(self.ID) + ' phase ' + str(self.phase) + ' started at ' + phase_time)
        if self.tracker:
            self.tracker.log('trial ' + str(self.ID) + ' phase ' + str(self.phase) + ' started at ' + phase_time )
            time_module.sleep(0.0005)

    def event(self):
        for ev in event.getKeys():
            self.key_event(ev)

        
class MRITrial(Trial):


    def __init__(self, *args, **kwargs):
        super(MRITrial, self).__init__(*args, **kwargs)
    
    def draw(self):
        super(MRITrial, self).draw()

    def key_event(self, key):
        if key == self.session.mri_trigger_key:
            self.session.mri_trigger()

        super(MRITrial, self).key_event(key)

    def event(self):
        if self.session.simulate_mri_trigger:
            current_time = self.session.clock.getTime()
            if current_time - self.session.target_trigger_time > 0:
                self.key_event(key=self.session.mri_trigger_key)
                logging.critical('Simulated trigger at %s' % current_time)

        super(MRITrial, self).event()
