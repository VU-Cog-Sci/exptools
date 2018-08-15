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
import yaml
from collections import OrderedDict


list_vars = [('screen', 'physical_screen_size'),
             ('screen', 'gamma_scale'),
             ('screen', 'background_color'),
             ('screen', 'size'),
             ('screen', 'max_lums')]

boolean_vars = [('screen', 'wait_blanking'),
                ('screen', 'full_screen'),
                ('screen', 'mouse_visible')]

str_vars = [('mri', 'mri_trigger_key'),]


def get_config(path=None, context=None):

    if path is None:
        path = os.path.join(os.path.abspath(os.getcwd()))
    
    yml_file = os.path.join(path, 'settings.yml')
    exp_config_file = os.path.join(path, 'exp_config.cfg')

    if os.path.isfile(yml_file):
        return YamlConfig(yml_file)

    elif os.path.isfile(exp_config_file):
        return ExptoolsConfig(exp_config_file)

    else:
        raise Exception('No valid configuration file has been found')


class ExpToolsConfig(object):

    def __init__(self, config_file):

        self._config = configparser.ConfigParser()
        self._config.read(config_file)


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

class YamlConfig(object):

    def __init__(self, 
                 yml_file,
                 context=None):

        with open(yml_file) as f:
            self.data = _ordered_load(f)
    
        if 'global' not in self.data:
            raise ValueError('no "global" condition in settings.yml!')

        if context is None:
            if len(self.data) == 1:
                self.context = 'global'
            else:
                for k in self.data.keys():
                    if k != 'global':
                        default_context = k
                        break

                context = raw_input('Context [{}]? '.format(default_context))

                if context == '':
                    self.context = default_context
                else:
                    if context not in self.data:
                        raise ValueError('Context {} does not exist'.format(context))
                    self.context = context

                print('Context is set to: {}'.format(self.context))

        self.config_dict = self.data['global']

        for key in self.config_dict:
            if key in self.data[self.context]:
                self.config_dict[key].update(self.data[self.context][key])

        for key in self.data[self.context]:
            if key not in self.config_dict:
                self.config_dict[key] = self.data[self.context][key]

    
    def get(self, section, option):
        return self.config_dict[section][option]

    def set(self, section, option, value):
        self.config_dict[section][option] = value


def test_exptools_config():
    config = ExpToolsConfig()
    assert('screen' in config._config.sections())

def _ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):

    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)
