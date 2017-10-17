# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Tests for the engine utils module
"""
"""
Session.py

Created by Tomas HJ Knapen on 2009-11-26.
Copyright (c) 2009 TK. All rights reserved.
"""

from psychopy import visual, core, event, misc, logging
import pygame
#from pygame.locals import *
from scipy.io import wavfile
import datetime
import os
import pickle as pkl

import pyaudio, wave
import numpy as np

import pygaze
from pygaze import libscreen 
from pygaze import eyetracker

from .. import config


class Session(object):
    """Session is a main class that creates screen and file properties"""
    def __init__(self, subject_initials, index_number, **kwargs):
        super(Session, self).__init__()
        self.subject_initials = subject_initials
        self.index_number = index_number
        
        self.clock = core.Clock()
        
        self.outputDict = {'parameterArray': [], 'eventArray' : []}
        self.events = []
        self.stopped = False
        self.logging = logging

        self.create_output_filename()

        engine = kwargs.pop('engine', 'pygaze')
        self.create_screen(engine=engine, **kwargs)

        self.start_time = self.clock.getTime()
    
    def create_screen(self, engine='pygaze', **kwargs):

         #Set arguments from config file or kwargs
        for argument in ['size', 'full_screen', 'background_color', 'gamma_scale',
                         'physical_screen_size', 'physical_screen_distance',
                         'max_lums', 'wait_blanking', 'screen_nr', 'mouse_visible']:
            value = kwargs.pop(argument, config.get('screen', argument))
            setattr(self, argument, value)

        if engine == 'pygaze':
            setattr(pygaze.settings, 'FULLSCREEN', self.full_screen)
            self.display = libscreen.Display(disptype='psychopy', 
                                             dispsize=self.size, 
                                             fgc=(255,0,0), 
                                             bgc=list((255*bgl for bgl in self.background_color)), 
                                             screennr=int(self.screen_nr),
                                             mousevisible=self.mouse_visible,
                                             fullscr=self.full_screen,)
                
            self.screen = pygaze.expdisplay
        elif engine == 'psychopy':   
            self.screen = visual.Window(size=self.size, 
                                        fullscr=self.full_screen, 
                                        screen=int(self.screen_nr),
                                        allowGUI=True, 
                                        units='pix', 
                                        allowStencil=True, 
                                        rgb=self.background_color, 
                                        waitBlanking=self.wait_blanking, 
                                        useFBO=True,
                                        winType='pyglet')

        self.screen.setMouseVisible(self.mouse_visible)
        event.Mouse(visible=self.mouse_visible, win=self.screen)

        self.screen.setColor(self.background_color)
        
        self.screen.background_color = self.background_color
        self.screen_pix_size = self.size

        self.screen_height_degrees = 2.0 * 180.0/np.pi * np.arctan((self.physical_screen_size[1]/2.0)/self.physical_screen_distance)

        self.pixels_per_degree = (self.size[1]) / self.screen_height_degrees

        self.centimeters_per_degree = self.physical_screen_size[1] / self.screen_height_degrees
        self.pixels_per_centimeter = self.pixels_per_degree / self.centimeters_per_degree

        self.screen.flip()

    def stop(self):
        self.stopped = True
    
    def create_output_filename(self, data_directory = 'data'):
        """create output file"""
        now = datetime.datetime.now()
        opfn = now.strftime("%Y-%m-%d_%H.%M.%S")
        
        if not os.path.isdir(data_directory):
            os.mkdir(data_directory)
            
        self.output_file = os.path.join(data_directory, self.subject_initials + '_' + str(self.index_number) + '_' + opfn )
    
    def open_input_file(self):
        """
        This method opens a pickle file that has input data in it.
        we assume the input data consists of two arrays - one for parameters and one for timings. 
        the two arrays' rows will be trials.
        """
        self.input_file_name = self.index_number + '.pkl'
        ipf = open(self.input_file_name)
        self.input_data = pkl.load(ipf)
        ipf.close()
    
    def create_input_data(self, save = False):
        """
        This method should be provided by subclasses that create input data on the fly
        """
        pass
    
    def parse_input_data(self):
        """
        We assume that the pickle file used as input will be an array, 
        the rows of which will be the requested trials.
        """
        self.nr_trials = len(self.input_data)
    
    def close(self):
        """close screen and save data"""
        pygame.mixer.quit()
        self.screen.close()
        parsopf = open(self.output_file + '_outputDict.pkl', 'a')
        pkl.dump(self.outputDict,parsopf)
        parsopf.close()
    
    def play_sound(self, sound_index = '0'):
        """docstring for play_sound"""
        if type(sound_index) == int:
            sound_index = str(sound_index)
        # assuming 44100 Hz, mono channel np.int16 format for the sounds
        stream_data = self.sounds[sound_index]
        
        self.frame_counter = 0
        def callback(in_data, frame_count, time_info, status):
            data = stream_data[self.frame_counter:self.frame_counter+frame_count]
            self.frame_counter += frame_count
            return (data, pyaudio.paContinue)

        # open stream using callback (3)
        stream = self.pyaudio.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=44100,
                        output=True,
                        stream_callback=callback)

        stream.start_stream()
        # stream.write(stream_data)

    def play_np_sound(self, sound_array):
        # assuming 44100 Hz, mono channel np.int16 format for the sounds
        
        self.frame_counter = 0
        def callback(in_data, frame_count, time_info, status):
            data = sound_array[self.frame_counter:self.frame_counter+frame_count]
            self.frame_counter += frame_count
            return (data, pyaudio.paContinue)

        # open stream using callback (3)
        stream = self.pyaudio.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=44100,
                        output=True,
                        stream_callback=callback)

        stream.start_stream()

    def deg2pix(self, deg):

        return deg * self.pixels_per_degree
            
class MRISession(Session):

    def __init__(self, 
                 subject_initials,
                 index_number,
                 tr=2, 
                 simulate_mri_trigger=True, 
                 mri_trigger_key=None, 
                 *args, 
                 **kwargs):


        super(MRISession, self).__init__(subject_initials, index_number, *args, **kwargs)

        self.simulate_mri_trigger = simulate_mri_trigger

        if mri_trigger_key is None:
            self.mri_trigger_key = config.get('mri', 'mri_trigger_key')    
        else:
            self.mri_trigger_key = mri_trigger_key

        self.time_of_last_tr = self.clock.getTime()


        self.tr = tr
        self.current_tr = 0
        self.target_trigger_time = self.start_time + self.tr

    def mri_trigger(self):
        self.time_of_last_tr = self.clock.getTime()
        self.current_tr += 1
        self.target_trigger_time = self.start_time + (self.current_tr + 1) * self.tr

        logging.critical('Registered MRI trigger')

class EyelinkSession(Session):
    """docstring for EyelinkSession"""
    def __init__(self, subject_initials, index_number, tracker_on=0, *args, **kwargs):

        super(EyelinkSession, self).__init__(subject_initials, index_number, *args, **kwargs)

        for argument in ['n_calib_points', 'sample_rate', 'calib_size', 'x_offset']:
            value = kwargs.pop(argument, config.get('eyetracker', argument))
            setattr(self, argument, value)

        if tracker_on == 1:
            self.create_tracker(tracker_on=True, 
                                calibration_type='HV%d'%self.n_calib_points, 
                                sample_rate=self.sample_rate)
            if self.tracker != None:
                self.tracker_setup()
        elif tracker_on == 2:
            # self.create_tracker(auto_trigger_calibration = 1, calibration_type = 'HV9')
            # if self.tracker_on:
            #     self.tracker_setup()
           # how many points do we want:
            n_points = self.n_calib_points

            # order should be with 5 points: center-up-down-left-right
            # order should be with 9 points: center-up-down-left-right-leftup-rightup-leftdown-rightdown 
            # order should be with 13: center-up-down-left-right-leftup-rightup-leftdown-rightdown-midleftmidup-midrightmidup-midleftmiddown-midrightmiddown
            # so always: up->down or left->right

            # creat tracker
            self.create_tracker(auto_trigger_calibration=0, 
                                calibration_type='HV%d'%self.n_calib_points, 
                                sample_rate=self.sample_rate)

            # it is setup to do a 9 or 5 point circular calibration, at reduced ecc

            # create 4 x levels:
            width = self.calib_size * self.size[1]
            x_start = (self.size[0]-width)/2
            x_end = self.size[0]-(self.size[0]-width)/2
            x_range = np.linspace(x_start,x_end,5) + self.x_offset
            y_start = (self.size[1]-width)/2
            y_end = self.size[1]-(self.size[1]-width)/2
            y_range = np.linspace(y_start,y_end,5) 

            # set calibration targets    
            cal_center = [x_range[2],y_range[2]]
            cal_left = [x_range[0],y_range[2]]
            cal_right = [x_range[4],y_range[2]]
            cal_up = [x_range[2],y_range[0]]
            cal_down = [x_range[2],y_range[4]]
            cal_leftup = [x_range[1],y_range[1]]
            cal_rightup = [x_range[3],y_range[1]]
            cal_leftdown = [x_range[1],y_range[3]]
            cal_rightdown = [x_range[3],y_range[3]]            
            
            # create 4 x levels:
            width = self.eyelink_calib_size*0.75 * self.size[1]
            x_start = (self.size[0]-width)/2
            x_end = self.size[0]-(self.size[0]-width)/2
            x_range = np.linspace(x_start,x_end,5) + self.x_offset
            y_start = (self.size[1]-width)/2
            y_end = self.size[1]-(self.size[1]-width)/2
            y_range = np.linspace(y_start,y_end,5) 

            # set calibration targets    
            val_center = [x_range[2],y_range[2]]
            val_left = [x_range[0],y_range[2]]
            val_right = [x_range[4],y_range[2]]
            val_up = [x_range[2],y_range[0]]
            val_down = [x_range[2],y_range[4]]
            val_leftup = [x_range[1],y_range[1]]
            val_rightup = [x_range[3],y_range[1]]
            val_leftdown = [x_range[1],y_range[3]]
            val_rightdown = [x_range[3],y_range[3]]   

            # get them in the right order
            if n_points == 5:
                cal_xs = np.round([cal_center[0],cal_up[0],cal_down[0],cal_left[0],cal_right[0]])
                cal_ys = np.round([cal_center[1],cal_up[1],cal_down[1],cal_left[1],cal_right[1]])
                val_xs = np.round([val_center[0],val_up[0],val_down[0],val_left[0],val_right[0]])
                val_ys = np.round([val_center[1],val_up[1],val_down[1],val_left[1],val_right[1]])
            elif n_points == 9:
                cal_xs = np.round([cal_center[0],cal_up[0],cal_down[0],cal_left[0],cal_right[0],cal_leftup[0],cal_rightup[0],cal_leftdown[0],cal_rightdown[0]])
                cal_ys = np.round([cal_center[1],cal_up[1],cal_down[1],cal_left[1],cal_right[1],cal_leftup[1],cal_rightup[1],cal_leftdown[1],cal_rightdown[1]])         
                val_xs = np.round([val_center[0],val_up[0],val_down[0],val_left[0],val_right[0],val_leftup[0],val_rightup[0],val_leftdown[0],val_rightdown[0]])
                val_ys = np.round([val_center[1],val_up[1],val_down[1],val_left[1],val_right[1],val_leftup[1],val_rightup[1],val_leftdown[1],val_rightdown[1]])                     
            #xs = np.round(np.linspace(x_edge,self.size[0]-x_edge,n_points))
            #ys = np.round([self.ywidth/3*[1,2][pi%2] for pi in range(n_points)])

            # put the points in format that eyelink wants them, which is
            # calibration_targets / validation_targets: 'x1,y1 x2,y2 ... xz,yz'
            calibration_targets = ' '.join(['%d,%d'%(cal_xs[pi],cal_ys[pi]) for pi in range(n_points)])
            # just copy calibration targets as validation for now:
            #validation_targets = calibration_targets
            validation_targets = ' '.join(['%d,%d'%(val_xs[pi],val_ys[pi]) for pi in range(n_points)])

            # point_indices: '0, 1, ... n'
            point_indices = ', '.join(['%d'%pi for pi in range(n_points)])

            # and send these targets to the custom calibration function:
            self.custom_calibration(calibration_targets=calibration_targets,
                validation_targets=validation_targets,point_indices=point_indices,
                n_points=n_points,randomize_order=True,repeat_first_target=True,)
            # reapply settings:
            self.tracker_setup()
        else:
            self.create_tracker(tracker_on=False)
    
    def create_tracker(self, 
                        tracker_on=True, 
                        sensitivity_class=0, 
                        split_screen=False, 
                        screen_half='L', 
                        auto_trigger_calibration=1, 
                        calibration_type='HV9', 
                        sample_rate=1000):
        """
        tracker sets up the connection and inputs the parameters.
        only start tracker after the screen is taken, its parameters are set,
         and output file names are created.
        """

        self.eyelink_temp_file = self.subject_initials[:2] + '_' + str(self.index_number) + '_' + str(np.random.randint(99)) + '.edf'

        if tracker_on:
            # create actual tracker
            # try:
            self.tracker = eyetracker.EyeTracker(self.display, trackertype='eyelink', resolution=self.display.dispsize, data_file=self.eyelink_temp_file, bgc=self.display.bgc)
            self.tracker_on = True
            # except:
            #     print('\ncould not connect to tracker')
            #     self.tracker = None
            #     self.tracker_on = False
            #     self.eye_measured, self.sample_rate, self.CR_mode, self.file_sample_filter, self.link_sample_filter = 'N', sample_rate, 1, 1, 1

            #     return
        else:
            # not even create dummy tracker
            self.tracker = None
            self.tracker_on = False
            return

        self.apply_settings(sensitivity_class=sensitivity_class, 
                            split_screen=split_screen, 
                            screen_half=screen_half, 
                            auto_trigger_calibration=auto_trigger_calibration, 
                            calibration_type=calibration_type, 
                            sample_rate=sample_rate)

    def custom_calibration(self,calibration_targets,validation_targets,point_indices,n_points,
        randomize_order=0,repeat_first_target=1):
        
        # send the messages:
        self.tracker.send_command('calibration_type = HV%d'%n_points  )
        self.tracker.send_command('generate_default_targets = NO')
        self.tracker.send_command('randomize_calibration_order %d'%randomize_order)
        self.tracker.send_command('randomize_validation_order %d'%randomize_order)
        self.tracker.send_command('cal_repeat_first_target  %d'%repeat_first_target)
        self.tracker.send_command('val_repeat_first_target  %d'%repeat_first_target)

        if repeat_first_target:
            n_points+=1
         
        self.tracker.send_command('calibration_samples=%d'%n_points)
        self.tracker.send_command('calibration_sequence=%s'%point_indices)
        self.tracker.send_command('calibration_targets = %s'%calibration_targets)
         
        self.tracker.send_command('validation_samples=%d'%n_points)
        self.tracker.send_command('validation_sequence=%s'%point_indices)
        self.tracker.send_command('validation_targets = %s'%validation_targets)

        
    def apply_settings(self, sensitivity_class = 0, split_screen = False, screen_half = 'L', auto_trigger_calibration = True, sample_rate = 1000, calibration_type = 'HV9', margin = 60):
        
        # set EDF file contents 
        self.tracker.send_command("file_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON")
        # self.tracker.send_command("file_sample_filter = LEFT,RIGHT,GAZE,SACCADE,BLINK,MESSAGE,AREA")#,GAZERES,STATUS,HTARGET")
        self.tracker.send_command("file_sample_data = LEFT,RIGHT,GAZE,AREA,GAZERES,STATUS,HTARGET")
        # set link da (used for gaze cursor) 
        self.tracker.send_command("link_event_filter = LEFT,RIGHT,FIXATION,FIXUPDATE,SACCADE,BLINK")
        self.tracker.send_command("link_sample_data = GAZE,GAZERES,AREA,HREF,PUPIL,STATUS")
        self.tracker.send_command("link_event_data = GAZE,GAZERES,AREA,HREF,VELOCITY,FIXAVG,STATUS")
        # set furtheinfo
        self.tracker.send_command("screen_pixel_coords =  0 0 %d %d" %(self.screen_pix_size[0], self.screen_pix_size[1]))
        self.tracker.send_command("pupil_size_diameter = %s"%('YES'));
        self.tracker.send_command("heuristic_filter %d %d"%([1, 0][sensitivity_class], 1))
        self.tracker.send_command("sample_rate = %d" % sample_rate)
        
        # settings tt address saccade sensitivity - to be set with sensitivity_class parameter. 0 is cognitive style, 1 is pursuit/neurological style
        self.tracker.send_command("saccade_velocity_threshold = %d" %[30, 22][sensitivity_class])
        self.tracker.send_command("saccade_acceleration_threshold = %d" %[9500, 5000][sensitivity_class])
        self.tracker.send_command("saccade_motion_threshold = %d" %[0.15, 0][sensitivity_class])
        
#       self.tracker.send_command("file_sample_control = 1,0,0")
        self.tracker.send_command("screen_phys_coords = %d %d %d %d" %(-self.physical_screen_size[0] / 2.0, self.physical_screen_size[1] / 2.0, self.physical_screen_size[0] / 2.0, -self.physical_screen_size[1] / 2.0))
        self.tracker.send_command("simulation_screen_distance = " + str(self.physical_screen_distance))
        
        if auto_trigger_calibration:
            self.tracker.send_command("enable_automatic_calibration = YES")
        else:
            self.tracker.send_command("enable_automatic_calibration = NO")
        
        # for binocular stereo-setup need to adjust the calibration procedure to sample only points on the left/right side of the screen. This allows only HV9 calibration for now.
            # standard would be:
            # self.tracker.).send_command("calibration_targets = 320,240 320,40 320,440 40,240 600,240 40,40 600,40, 40,440 600,440")
            # ordering of points:
        #   ;; FOR 9-SAMPLE ALGORITHM:
        #   ;; POINTS MUST BE ORDERED ON SCREEN:
        #   ;; 5 1 6
        #   ;; 3 0 4
        #   ;; 7 2 8

        #   ;; ordering for points in bicubic ("HV13", 13 pt) cal
        #   ;; Point order: 6 2 7
        #   ;;   10 11
        #   ;;   4 1 5
        #   ;;   12 13
        #   ;;   8 3 9
        if split_screen:
            self.tracker.send_command("calibration_type = HV9")
            self.tracker.send_command("generate_default_targets = NO")
            
            sh, nsw = self.screen.size[1], self.screen.size[0]/2
            points = np.array([[nsw/2, sh/2], [nsw/2, sh-margin], [nsw/2, margin], [margin, sh/2], [nsw-margin, sh/2], [margin, sh - margin], [nsw - margin, sh - margin], [margin, margin], [nsw - margin, margin]])
            if screen_half == 'R':
                points[:,0] += nsw
            points_string = ''
            for p in points:
                points_string += "%s,%s " % tuple(p)
            points_string = points_string[:-1] # delete last space
            self.tracker.send_command("calibration_targets = " % points_string)
            self.tracker.send_command("validation_targets = " % points_string)
        else:
            self.tracker.send_command("calibration_type = " + calibration_type)
            
    def tracker_setup(self, sensitivity_class = 0, split_screen = False, screen_half = 'L', auto_trigger_calibration = True, calibration_type = 'HV9', sample_rate = 1000):
        if self.tracker.connected():
                        
            self.tracker.calibrate()

            # re-set all the settings to be sure of sample rate and filter and such that may have been changed during the calibration procedure and the subject pressing all sorts of buttons
            self.apply_settings(sensitivity_class = sensitivity_class, split_screen = split_screen, screen_half = screen_half, auto_trigger_calibration = auto_trigger_calibration, calibration_type = calibration_type, sample_rate = sample_rate )
            
            # we'll record the whole session continuously and parse the data afterward using the messages sent to the eyelink.
            self.tracker.start_recording()
            # for that, we'll need the pixel size and the like. 
            self.tracker.log('degrees per pixel ' + str(self.pixels_per_degree) )
            # now, we want to know how fast we're sampling, really
#           self.eye_measured, self.sample_rate, self.CR_mode, self.file_sample_filter, self.link_sample_filter = self.tracker.getModeData()
            self.sample_rate = sample_rate
    
    def drift_correct(self, position = None):
        """docstring for drift_correct"""
        if self.tracker.connected():
            if position == None:    # standard is of course centered on the screen.
                position = [self.screen.size[0]/2,self.screen.size[1]/2]
            while 1:
                # Does drift correction and handles the re-do camera setup situations
                error = self.tracker.doDriftCorrect(position[0],position[1],1,1)
                if error != 27: 
                    break;
                else:
                    self.tracker_setup()
    
    def eye_pos(self):
        if self.tracker:
            return self.tracker.sample() # check for new sample update
            # if(dt != None):
            #   # Gets the gaze position of the latest sample,
            #   if dt.isRightSample():
            #       gaze_position = dt.getRightEye().getGaze()
            #       return gaze_position[0],gaze_position[1] # self.screen.size[1]-
            #   elif dt.isLeftSample():
            #       gaze_position = dt.getLeftEye().getGaze()
            #       return gaze_position[0],gaze_position[1] # self.screen.size[1]-
            # return 0,self.screen.size[1]-0
        else:
            pygame.event.pump()
            (x,y) = pygame.mouse.get_pos()
            y = self.screen.size[1]-y
            return x,y
        
    def detect_saccade(self, algorithm_type = 'velocity', threshold = 0.25, direction = None, fixation_position = None, max_time = 1.0 ):
        """
        detect_saccade tries to detect a saccade based on position (needs fixation_position argument) or velocity (perhaps a direction argument?) information. 
        It can be 'primed' with a vector giving the predicted direction of the impending saccade. 
        detect_saccade looks for a saccade between call_time (= now) and max_time+call_time
        """
        no_saccade = True
        start_time = core.getTime()
        if algorithm_type == 'velocity':
            sample_array = np.zeros((max_time * self.sample_rate, 2), dtype = np.float32)
            velocity_array = np.zeros((max_time * self.sample_rate, 2), dtype = np.float32)
            f = np.array([1,1,2,3], dtype = np.float32)/7.0
            nr_samples = 1
            sample_array[0,:] = self.eye_pos()
            velocity_array[0,:] = 0.001, 0.001
            if direction != None: # make direction a unit vector if it is an argument to this function
                direction = direction / np.linalg.norm(direction)
            
            while no_saccade:
                saccade_polling_time = core.getTime()
                sample_array[nr_samples][:] = self.eye_pos()
                if (sample_array[nr_samples-1][0] != sample_array[nr_samples][0]) or (sample_array[nr_samples-1][1] != sample_array[nr_samples][1]):
                    velocity_array[nr_samples][:] = sample_array[nr_samples][:] - sample_array[nr_samples-1][:]
                    if nr_samples > 3:
                        # scale velocities according to x and y median-based standard deviations, as in engbert & mergenthaler, 2006
                        med_scaled_velocity = velocity_array[:nr_samples]/np.mean(np.sqrt(((velocity_array[:nr_samples] - np.median(velocity_array[:nr_samples], axis = 0))**2)), axis = 0)
                        if direction != None: 
                            # scale the velocity array according to the direction in the direction argument before thresholding
                            # assuming direction is a x,y unit vector specifying the expected direction of the impending saccade
                            if np.inner(med_scaled_velocity[nr_samples], direction) > threshold:
                                no_saccade = False
                        if np.linalg.norm(med_scaled_velocity[-1]) > threshold:
                            no_saccade = False
                    nr_samples += 1
                if ( saccade_polling_time - start_time ) > max_time:
                    no_saccade = False
            
        if algorithm_type == 'position' or not self.tracker:
            if fixation_position == None:
                fixation_position = np.array(self.eye_pos())
            while no_saccade:
                saccade_polling_time = core.getTime()
                ep = np.array(self.eye_pos())
        #       print ep, fixation_position, threshold, np.linalg.norm(ep - fixation_position) / self.pixels_per_degree
                if (np.linalg.norm(ep - fixation_position) / self.pixels_per_degree) > threshold:
                    # eye position is outside the safe zone surrounding fixation - swap the buffers to change saccade target position
                    no_saccade = False
        #           print '\n'
                if ( saccade_polling_time - start_time ) > max_time:
                    no_saccade = False
            
        if algorithm_type == 'eyelink':
            while no_saccade:
                self.tracker.wait_for_saccade_start()
                saccade_polling_time = core.getTime()
                # ev = 
                # if ev == 5: # start of a saccade
                #   no_saccade = False
                # if ( saccade_polling_time - start_time ) > max_time:
                #   no_saccade = False
            
        return saccade_polling_time
            
    
    def close(self):
        if self.tracker:
            if self.tracker.connected():
                self.tracker.stop_recording()
            # inject local file name into pygaze tracker and then close.
            self.tracker.local_data_file = self.output_file + '.edf'
            self.tracker.close()
        super(EyelinkSession, self).close()
    
    def play_sound(self, sound_index = '1'):
        """docstring for play_sound"""
        super(EyelinkSession, self).play_sound(sound_index = sound_index)
        if self.tracker != None:
            self.tracker.log('sound ' + str(sound_index) + ' at ' + str(core.getTime()) )


class StarStimSession(EyelinkSession):
    """StarStimSession adds starstim EEG trigger functionality to the EyelinkSession.
    It assumes an active recording, using NIC already connected over bluetooth.
    Triggers land in the file that's already set up and recording.
    """
    def __init__(self, subject_initials, index_number, connect_to_starstim = False, TCP_IP = '10.0.1.201', TCP_PORT = 1234):
        super(StarStimSession, self).__init__(subject_initials, index_number)
        self.setup_starstim_connection(TCP_IP = TCP_IP, TCP_PORT = TCP_PORT, connect_to_starstim = connect_to_starstim)

    def setup_starstim_connection(self, TCP_IP = '10.0.1.201', TCP_PORT = 1234, connect_to_starstim = True):
        """setup_starstim_connection opens a connection to the starstim to its standard ip address
        and standard (trigger) port. For controlling the recordings etc, we need tcp port 1235, it seems.
        more on that later. 
        """
        if connect_to_starstim:
            self.star_stim_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.star_stim_socket.connect((TCP_IP, TCP_PORT))
            self.star_stim_connected = True
        else:
            self.star_stim_connected = False

    def close_starstim_connection(self):
        if self.star_stim_connected:
            self.star_stim_socket.close()

    def send_starstim_trigger(self, trigger = 1):
        if self.star_stim_connected:
            self.star_stim_socket.sendall('<TRIGGER>%i</TRIGGER>'%trigger)

    def close(self):
        super(StarStimSession, self).close()
        if self.star_stim_connected:
            self.close_starstim_connection()


class SoundSession(Session):


    def __init__(self, *args, **kwargs):
        self.setup_sound_system()
        super(SoundSession, self).__init__(*args, **kwargs)

    def setup_sound_system(self):
        """initialize pyaudio backend, and create dictionary of sounds."""
        self.pyaudio = pyaudio.PyAudio()
        self.sound_files = subprocess.Popen('ls ' + os.path.join(os.environ['EXPERIMENT_HOME'], 'sounds', '*.wav'), shell=True, stdout=subprocess.PIPE).communicate()[0].split('\n')[0:-1]
        self.sounds = {}
        for sf in self.sound_files:
            self.read_sound_file(file_name = sf)

    def read_sound_file(self, file_name, sound_name = None):
        """Read sound file from file_name, and append to self.sounds with name as key"""
        if sound_name == None:
            sound_name = os.path.splitext(os.path.split(file_name)[-1])[0]

        rate, data = wavfile.read(file_name)
        # create stream data assuming 2 channels, i.e. stereo data, and use np.float32 data format
        stream_data = data.astype(np.int16)

        # check data formats - is this stereo sound? If so, we need to fix it. 
        wf = wave.open(file_name, 'rb')
        if wf.getnchannels() == 2:
            stream_data = stream_data[::2]

        self.sounds.update({sound_name: stream_data})

def test_MRISession_simulation():
    from .trial import Trial

    session = MRISession('GdH', 1)
    session.create_screen()

    trial = Trial(session=session)
    trial.draw()

    core.wait(2)
    trial.draw()

    logging.console.setLevel(logging.DEBUG)
    logging.info('Current TR: %s\n\rTime last TR: %s' % (session.current_tr, session.time_of_last_tr, ))
    assert(session.current_tr > 0) 




