# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
'''
Created on 16 Aug 2017
Based on Nipype Configuration file
logging options : INFO, DEBUG
@author: Gilles de Hollander '''

import configparser
import os
import exptools 
import json


list_vars = [('screen', 'physical_screen_size'),
             ('screen', 'gamma_scale'),
             ('screen', 'background_color'),
             ('screen', 'size'),
             ('screen', 'max_lums')]

boolean_vars = [('screen', 'wait_blanking'),
                ('screen', 'full_screen'),
                ('screen', 'mouse_visible')]

str_vars = [('mri', 'mri_trigger_key'),]

class ExpToolsConfig(object):

    def __init__(self):

        self._config = configparser.ConfigParser()
        
        # config_dir = os.path.expanduser('~/.exptools')
        # config_file = os.path.join(config_dir, 'exptools.cfg')

        # default_file = os.path.join(exptools.__path__[0], 'default_config.cfg')
        exp_config_file = os.path.join(os.path.abspath(os.getcwd()), 'exp_config.cfg')

        self._config.read(exp_config_file)

        # if os.path.exists(config_dir):
        #     self._config.read(config_file)

    def get(self, section, option):
        if (section, option) in list_vars:
            return json.loads(self._config.get(section, option))
        elif (section, option) in boolean_vars:
            return self._config.getboolean(section, option)
        elif (section, option) in str_vars:
            return self._config.get(section, option)
        else:
            return float(self._config.get(section, option))

    def set(self, section, option, value):
        if isinstance(value, bool) or isinstance(value, list):
            value = str(value)

        return self._config.set(section, option, value)



def test_exptools_config():
    config = ExpToolsConfig()
    assert('screen' in config._config.sections())

