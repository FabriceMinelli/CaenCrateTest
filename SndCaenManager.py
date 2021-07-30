import os
import toml
import numpy as np


from pycaenhv.wrappers import init_system, deinit_system, get_board_parameters, get_crate_map, get_channel_parameter, set_channel_parameter, get_channel_parameter_property
from pycaenhv.helpers import channel_info
from pycaenhv.enums import CAENHV_SYSTEM_TYPE, LinkType
from pycaenhv.errors import CAENHVError


class SndCaenManager():
    
    def __init__(self, confPath):
        self.config = toml.load(confPath)
        self.handles = []
        for crate in self.config['crates']:
            system_type = CAENHV_SYSTEM_TYPE[crate['module']]
            link_type = LinkType[crate['linktype']]
            self.handles.append(init_system(system_type, link_type, crate['address'], crate['username'], crate['password']))

        try:
            self.crates_maps = []
            nb_crate = 0
            for handle in self.handles:  
                self.crates_maps.append(get_crate_map(handle))
                #print(f"Crate {nb_crate}: ")
                #print(f"Got handle: {handle}")
                #print((self.crates_maps[-1]['channels']))
                #for name, value in self.crates_maps[-1].items():
                #    print(name, value)
                #board_parameters = get_board_parameters(handle, board)
                #print(f"Board parameters: {board_parameters}")

        except CAENHVError as err:
            print(f"Got error: {err}\nExiting ...")



    def getConfigProperty(self, DAQ: str, mode: str):
        """
        Get the crate, board and channel number in the config file. DAQ is the board ('m1x1'...) and mode is either 'board' for LV or 'bias' for HV
        """
        crate = self.config[mode][DAQ]['crate']
        board = self.config[mode][DAQ]['board']
        channel = self.config[mode][DAQ]['channel']
        return crate, board, channel

    """
    def functionTest(self, DAQ: str, mode: str):
        crate, board, channel = self.getConfigProperty(DAQ, mode)
        print(crate, board, channel)
    """
        

    def switchLV(self, on: bool, DAQs = None):
        """
        Switch on/off the power of the low voltage.
        If DAQs = None, it switches on all the DAQ boards, otherwise give an array (['m1x1', 'm1x2',...])
        """
        if DAQs == None:
            for DAQ in self.config['board']:
                if DAQ == 'default':
                    pass
                else:
                    crate, board, channel = self.getConfigProperty(DAQ, 'board')
                    set_channel_parameter(self.handles[crate], board, channel, 'Pw', on)
        else:
            for DAQ in DAQs:
                if DAQ in self.config['board']:
                    crate, board, channel = self.getConfigProperty(DAQ, 'board')
                    set_channel_parameter(self.handles[crate], board, channel, 'Pw', on)                
                else:
                    print(f"Module {DAQ} does not exist")


    def override_OV(self, OV: int, DAQs = None): #Give ['m1x1'] or ['m1x1', 'm2x2',....]. None set on all the DAQ boards
        """
        Allows to chose the overvoltage of the different DAQ boards.
        If DAQs = None, sets the OV on all the DAQ boards, otherwise give an array of strings
        """
        if DAQs == None:
            print('None')
            for DAQ in self.config['bias']:
                if DAQ == 'default':
                    pass
                else:
                    crate, board, channel = self.getConfigProperty(DAQ, 'bias')
                    try:
                        V = OV + self.config['bias'][DAQ]['v_offset_tofpet'] + self.config['bias'][DAQ]['v_bd']
                    except KeyError:
                        V = OV + self.config['bias']['default']['v_offset_tofpet'] + self.config['bias'][DAQ]['v_bd']
                    set_channel_parameter(self.handles[crate], board, channel, 'V0Set', V)
        else:
            for DAQ in DAQs:
                crate, board, channel = self.getConfigProperty(DAQ, 'bias')
                try:
                    V = OV + self.config['bias'][DAQ]['v_offset_tofpet'] + self.config['bias'][DAQ]['v_bd']
                except KeyError:
                    V = OV + self.config['bias']['default']['v_offset_tofpet'] + self.config['bias'][DAQ]['v_bd']
                set_channel_parameter(self.handles[crate], board, channel, 'V0Set', V)

    

    def switchHV(self, mode: str, DAQs = None):
        """
        Switch on/off the power of the High voltage. 3 modes : off = Power off, idle = Power on (OV = -10V), operation = Power on (OV = 3.5V) and on = Power on with the previous set OV
        If DAQs = None, it switches on all the DAQ boards, otherwise give an array (['m1x1', 'm1x2',...])
        """
        if DAQs == None:
            for DAQ in self.config['bias']:
                if DAQ == 'default':
                    pass
                else:
                    crate, board, channel = self.getConfigProperty(DAQ, 'bias')
                    if mode == 'off':
                        set_channel_parameter(self.handles[crate], board, channel, 'Pw', False)
                    elif mode == 'idle':
                        self.override_OV(-10, [DAQ])                   
                        set_channel_parameter(self.handles[crate], board, channel, 'Pw', True)
                    elif mode == 'operation':
                        self.override_OV(3.5, [DAQ])                   
                        set_channel_parameter(self.handles[crate], board, channel, 'Pw', True)
        else:
            for DAQ in DAQs:
                if DAQ in self.config['bias']:
                    crate, board, channel = self.getConfigProperty(DAQ, 'bias')
                    if mode == 'off':
                        set_channel_parameter(self.handles[crate], board, channel, 'Pw', False)
                    elif mode == 'idle':
                        self.override_OV(-10, [DAQ])                   
                        set_channel_parameter(self.handles[crate], board, channel, 'Pw', True)
                    elif mode == 'operation':
                        self.override_OV(3.5, [DAQ])                   
                        set_channel_parameter(self.handles[crate], board, channel, 'Pw', True)
                    elif mode == 'on':
                        set_channel_parameter(self.handles[crate], board, channel, 'Pw', True)

    def showChannelInfo(self, mode: str, DAQs = None):
        """
        Print all the parameters of the corresponding channels. If DAQs = None => print for all boards
        mode is either 'bias' for HV or 'board' for LV
        """
        if DAQs == None:
            for DAQ in self.config[mode]:
                if DAQ == 'default':
                    pass
                else:
                    crate, board, channel = self.getConfigProperty(DAQ, mode)
                    chan_info = channel_info(self.handles[crate], board, channel)
                    print(f'DAQ {DAQ} channel information:')
                    print(f'crate = {crate}, board = {board}, channel = {channel}')
                    for chan in chan_info:
                        print(chan)
                    print('^\n')
        else:
            for DAQ in DAQs:
                crate, board, channel = self.getConfigProperty(DAQ, mode)
                chan_info = channel_info(self.handles[crate], board, channel)
                print(f'DAQ {DAQ} channel information:')
                print(f'crate = {crate}, board = {board}, channel = {channel}')
                for chan in chan_info:
                    print(chan)
                print('^\n')

    def showChannelParameter(self, parameter: str, mode: str, DAQs = None):
        if DAQs == None:
            for DAQ in self.config[mode]:
                if DAQ == 'default':
                    pass
                else:
                    crate, board, channel = self.getConfigProperty(DAQ, mode)
                    parameter_value = get_channel_parameter(self.handles[crate], board, channel, parameter)
                    parameter_unit = get_channel_parameter_property(self.handles[crate], board, channel, parameter, 'Unit')
                    print(f'DAQ {DAQ} parameter {parameter} information : {parameter_value} {parameter_unit}')        
        else:
            for DAQ in DAQs:
                crate, board, channel = self.getConfigProperty(DAQ, mode)
                parameter_value = get_channel_parameter(self.handles[crate], board, channel, parameter)
                parameter_unit = get_channel_parameter_property(self.handles[crate], board, channel, parameter, 'Unit')
                print(f'DAQ {DAQ} parameter {parameter} information : {parameter_value} {parameter_unit}')        
        
                
    