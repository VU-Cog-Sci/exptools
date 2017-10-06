import numpy as np

class Trial(object):
    """base class for Trials"""
    def __init__(self, 
                    parameters={}, 
                    phase_durations=[], 
                    session=None, 
                    screen=None, 
                    tracker=None):
        super(Trial, self).__init__()
        self.parameters = parameters.copy()
        self.phase_durations = phase_durations
        self.screen = screen
        self.tracker = tracker
        self.session = session
        
        self.events = []
        self.phase = 0
        self.phase_times = [0.0 for i in range(len(self.phase_durations))]
        self.stopped = False
    
    def create_stimuli(self):
        pass
    
    def run(self):
        self.start_time = self.session.clock.getTime()
        if self.tracker:
            self.tracker.log('trial ' + str(self.ID) + ' started at ' + str(self.start_time) )
            self.tracker.send_command('record_status_message "Trial ' + str(self.ID) + '"')
        self.events.append('trial ' + str(self.ID) + ' started at ' + str(self.start_time))
        
        
    def stop(self):
        self.stop_time = self.session.clock.getTime()
        self.stopped = True
        if self.tracker:
            # pipe parameters to the eyelink data file in a for loop so as to limit the risk of flooding the buffer
            for k in self.parameters.keys():
                self.tracker.log('trial ' + str(self.ID) + ' parameter\t' + k + ' : ' + str(self.parameters[k]) )
                time_module.sleep(0.0001)
            self.tracker.log('trial ' + str(self.ID) + ' stopped at ' + str(self.stop_time) )
        self.session.outputDict['eventArray'].append(self.events)
        self.session.outputDict['parameterArray'].append(self.parameters)
        
    def key_event(self, event):
        if self.tracker:
            self.tracker.log('trial ' + str(self.ID) + ' event ' + str(event) + ' at ' + str(self.session.clock.getTime()) )
        self.events.append('trial ' + str(self.ID) + ' event ' + str(event) + ' at ' + str(self.session.clock.getTime()))
    
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
            time_module.sleep(0.0001)
        
    def check_phase_time(self):
        """
        check_phase_time checks the phase time of the present phase
        and implements alarms based on time. The transgression of an alarm time
        prompts the trial to either phase forward or stop, depending on the present phase.
        """
        # object variable to record all trial phase times in past and present
        self.phase_times[self.phase] = self.session.clock.getTime()
        # the first phase has no previous phase
        if self.phase == 0:
            previous_time = self.start_time
        elif self.phase > 0:
            previous_time = self.phase_times[self.phase - 1]
        # time elapsed since start of this phase
        this_phase_time = self.phase_times[self.phase] - previous_time
        # check for alarm
        if this_phase_time > self.phase_durations[self.phase]:
            # last trial stops, others phase forward
            if self.phase == (len(self.phase_durations) - 1):
                self.stopped = True
            else:
                self.phase_forward()
                # and, because trial phases should be instantaneously skipped if 
                # the phase duration is below 0, this function calls itself when phasing forward.
                self.check_phase_time()

