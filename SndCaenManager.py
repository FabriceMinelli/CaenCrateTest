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



    def getConfigProperty(self, daq: str, mode: str):
        """
        Get the crate, board and channel number in the config file. daq is the board ('m1x1'...) and mode is either 'board' for LV or 'bias' for HV
        """
        crate = self.config[mode][daq]['crate']
        board = self.config[mode][daq]['board']
        channel = self.config[mode][daq]['channel']
        return crate, board, channel

    """
    def functionTest(self, DAQ: str, mode: str):
        crate, board, channel = self.getConfigProperty(DAQ, mode)
        print(crate, board, channel)
    """
        

    def switchLV(self, on: bool, daqs = None):
        """
        Switch on/off the power of the low voltage.
        If daqs = None, it switches on all the DAQ boards, otherwise give an array (['m1x1', 'm1x2',...])
        """
        if daqs is None:
            for daq in self.config['board']:
                if daq == 'default':
                    pass
                else:
                    crate, board, channel = self.getConfigProperty(daq, 'board')
                    set_channel_parameter(self.handles[crate], board, channel, 'Pw', on)
        else:
            for daq in daqs:
                if daq in self.config['board']:
                    crate, board, channel = self.getConfigProperty(daq, 'board')
                    set_channel_parameter(self.handles[crate], board, channel, 'Pw', on)                
                else:
                    print(f"Module {daq} does not exist")


    def override_OV(self, OV: int, daqs = None): #Give ['m1x1'] or ['m1x1', 'm2x2',....]. None set on all the DAQ boards
        """
        Allows to chose the overvoltage of the different DAQ boards.
        If daq = None, sets the OV on all the DAQ boards, otherwise give an array of strings
        """
        if daqs is None:
            print('None')
            for daq in self.config['bias']:
                if daq == 'default':
                    pass
                else:
                    crate, board, channel = self.getConfigProperty(daq, 'bias')
                    try:
                        V = OV + self.config['bias'][daq]['v_offset_tofpet'] + self.config['bias'][daq]['v_bd']
                    except KeyError:
                        V = OV + self.config['bias']['default']['v_offset_tofpet'] + self.config['bias'][daq]['v_bd']
                    set_channel_parameter(self.handles[crate], board, channel, 'V0Set', V)
        else:
            for daq in daqs:
                crate, board, channel = self.getConfigProperty(daq, 'bias')
                try:
                    V = OV + self.config['bias'][daq]['v_offset_tofpet'] + self.config['bias'][daq]['v_bd']
                except KeyError:
                    V = OV + self.config['bias']['default']['v_offset_tofpet'] + self.config['bias'][daq]['v_bd']
                set_channel_parameter(self.handles[crate], board, channel, 'V0Set', V)

    

    def switchHV(self, mode: str, daqs = None):
        """
        Switch on/off the power of the High voltage. 4 modes : off = Power off, idle = Power on (OV = -10V), operation = Power on (OV = 3.5V) and on = Power on with the previous set OV
        If daqs = None, it switches on all the DAQ boards, otherwise give an array (['m1x1', 'm1x2',...])
        """
        if daqs is None:
            for daq in self.config['bias']:
                if daq == 'default':
                    pass
                else:
                    crate, board, channel = self.getConfigProperty(daq, 'bias')
                    if mode == 'off':
                        set_channel_parameter(self.handles[crate], board, channel, 'Pw', False)
                    elif mode == 'idle':
                        self.override_OV(-10, [daq])                   
                        set_channel_parameter(self.handles[crate], board, channel, 'Pw', True)
                    elif mode == 'operation':
                        self.override_OV(self.config['bias']['default']['ov'], [daq])                   
                        set_channel_parameter(self.handles[crate], board, channel, 'Pw', True)
                    elif mode == 'on':
                        set_channel_parameter(self.handles[crate], board, channel, 'Pw', True)
        else:
            for daq in daqs:
                if daq in self.config['bias']:
                    crate, board, channel = self.getConfigProperty(daq, 'bias')
                    if mode == 'off':
                        set_channel_parameter(self.handles[crate], board, channel, 'Pw', False)
                    elif mode == 'idle':
                        self.override_OV(-10, [daq])                   
                        set_channel_parameter(self.handles[crate], board, channel, 'Pw', True)
                    elif mode == 'operation':
                        self.override_OV(self.config['bias']['default']['ov'], [daq])                   
                        set_channel_parameter(self.handles[crate], board, channel, 'Pw', True)
                    elif mode == 'on':
                        set_channel_parameter(self.handles[crate], board, channel, 'Pw', True)

    def showChannelInfo(self, mode: str, daqs = None):
        """
        Print all the parameters of the corresponding channels. If daq = None => print for all boards
        mode is either 'bias' for HV or 'board' for LV
        """
        if daqs is None:
            for daq in self.config[mode]:
                if daq == 'default':
                    pass
                else:
                    crate, board, channel = self.getConfigProperty(daq, mode)
                    chan_info = channel_info(self.handles[crate], board, channel)
                    print(f'DAQ {daq} channel information:')
                    print(f'crate = {crate}, board = {board}, channel = {channel}')
                    for chan in chan_info:
                        print(chan)
                    print('^\n')
        else:
            for daq in daqs:
                crate, board, channel = self.getConfigProperty(daq, mode)
                chan_info = channel_info(self.handles[crate], board, channel)
                print(f'DAQ {daq} channel information:')
                print(f'crate = {crate}, board = {board}, channel = {channel}')
                for chan in chan_info:
                    print(chan)
                print('^\n')

    def showChannelParameter(self, parameter: str, mode: str, daqs = None):
        """
        Show the chosen parameter for the chosen DAQ boards.
        mode is either 'board' for LV or 'bias' for HV. 
        """
        if daqs is None:
            for daq in self.config[mode]:
                if daq == 'default':
                    pass
                else:
                    crate, board, channel = self.getConfigProperty(daq, mode)
                    parameter_value = get_channel_parameter(self.handles[crate], board, channel, parameter)
                    parameter_unit = get_channel_parameter_property(self.handles[crate], board, channel, parameter, 'Unit')
                    print(f'DAQ {daq} parameter {parameter} information : {parameter_value} {parameter_unit}')        
        else:
            for daq in daqs:
                crate, board, channel = self.getConfigProperty(daq, mode)
                parameter_value = get_channel_parameter(self.handles[crate], board, channel, parameter)
                parameter_unit = get_channel_parameter_property(self.handles[crate], board, channel, parameter, 'Unit')
                print(f'DAQ {daq} parameter {parameter} information : {parameter_value} {parameter_unit}')        

    
    def setLV(self, v = None, daqs = None):
        """
        Allows to set the LV value to the DAQ boards.
        if v = None => set the default value set in the config fule
        if daqs = None => put it on all boards, otherwise give "['m1x1',...]
        """
        if daqs is None:
            for daq in self.config['board']:
                if daq == 'default':
                    pass
                else:
                    crate, board, channel = self.getConfigProperty(daq, 'board')
                    if v is None:
                        set_channel_parameter(self.handles[crate], board, channel, 'V0Set', self.config['board']['default']['v'])
                        print('oui oui')
                    else:
                        set_channel_parameter(self.handles[crate], board, channel, 'V0Set', v)                     
        else:
            for daq in daqs:
                crate, board, channel = self.getConfigProperty(daq, 'board')
                if v is None:
                    set_channel_parameter(self.handles[crate], board, channel, 'V0Set', self.config['board']['default']['v'])
                else:
                    set_channel_parameter(self.handles[crate], board, channel, 'V0Set', v)
        
    def checkStatus(self, mode: str, daqs = None):
        """
        Print the status of the chosen boards.
        mode is either 'board' for LV and 'bias' for HV
        if daqs = None => put it on all boards, otherwise give "['m1x1',...]
        """
        if daqs is None:
            for daq in self.config[mode]:
                if daq == 'default':
                    pass
                else:
                    crate, board, channel = self.getConfigProperty(daq, mode)
                    parameter_value = get_channel_parameter(self.handles[crate], board, channel, 'Status')
                    if type(parameter_value) == int:
                        print(f'The board {daq} is working correctly.')   
                        print(parameter_value)             
                    else:
                        compteur = 0
                        for el in parameter_value:
                            if compteur == 0 and el == 1:
                                print(f'The board {daq} is in power-fail status')     
                            if compteur == 1 and el == 1:
                                print(f'The board {daq} has a firmware checksum error')  
                            if compteur == 2 and el == 1:
                                print(f'The board {daq} has a calibration error on HV')  
                            if compteur == 3 and el == 1:
                                print(f'The board {daq} has a calibration error on temperature') 
                            if compteur == 4 and el == 1:
                                print(f'The board {daq} is in under-temperature status')  
                            if compteur == 5 and el == 1:
                                print(f'The board {daq} is in over-temperature status')   
                            compteur += 1
        else:
            for daq in daqs:
                crate, board, channel = self.getConfigProperty(daq, mode)
                parameter_value = get_channel_parameter(self.handles[crate], board, channel, 'Status')
                if type(parameter_value) == int:
                        print(f'The board {daq} is working correctly.')                
                else:
                    compteur = 0
                    for el in parameter_value:
                        if compteur == 0 and el == 1:
                                print(f'The board {daq} is in power-fail status')     
                        if compteur == 1 and el == 1:
                                print(f'The board {daq} has a firmware checksum error')  
                        if compteur == 2 and el == 1:
                                print(f'The board {daq} has a calibration error on HV')  
                        if compteur == 3 and el == 1:
                                print(f'The board {daq} has a calibration error on temperature') 
                        if compteur == 4 and el == 1:
                                print(f'The board {daq} is in under-temperature status')  
                        if compteur == 5 and el == 1:
                            print(f'The board {daq} is in over-temperature status')   
                        compteur += 1