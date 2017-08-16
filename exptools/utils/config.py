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


class ExpToolsConfig(object):

    def __init__(self):

        self._config = configparser.ConfigParser()
        
        config_dir = os.path.expanduser('~/.exptools')
        config_file = os.path.join(config_dir, 'exptools.cfg')

        default_file = os.path.join(exptools.__path__[0], 'default_config.cfg')

        self._config.read(default_file)

        if os.path.exists(config_dir):
            self._config.read(config_file)

    def get(self, section, option):
        return json.loads(self._config.get(section, option))

    def set(self, section, option, value):
        if isinstance(value, bool):
            value = str(value)

        return self._config.set(section, option, value)



def test_exptools_config():
    config = ExpToolsConfig()
    assert('display' in config._config.sections())

