# midi2ts590 by Patrick EGLOFF aka TK5EP
#
#
# reads MIDI commands from a HERCULES DJcontrol compact controller
# each JOG, slider or button have a function assigned and sends KENWOOD remote commands to a TS590s via a COM port
# MIDI command are including the device number (0 to 4, depending on your setup), the MIDI status (depending on the kind of control), the control ID (depending on the device) and finally the control value
#
# v 0.1     15/02/17    first version
# v 0.2     15/01/2023  changed many small things, use of KwdCat library
# v 0.22    20/01/2023  added thread to poll radio and change mode/vfo accordingly on DJcontroller

__Title = "Remote control for TS590 with DJcontrol Compact"
__Version = "0.23"
__VersionDate = "20/01/2023"

# import libraries
import configparser                         #https://docs.python.org/3/library/configparser.html
import os
import sys
import argparse
import math
import time
from os import environ                      # following 2 lines are to hide pygame welcome message
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame.midi
from threading import Thread

## Import own libraries
from KwdCat import KwdCat

# global variables from a config file
import config
oldfwcw = 0
oldfwfsk = 0
oldsh = 0
oldis = 0
oldsl = 0
#########################################
# create some optional arguments for startup
# -h : help
# -v : make verbose for debugging
# -p : show COM ports
# -m : show MIDI ports
parser = argparse.ArgumentParser()
parser.add_argument("-m","--midi", help="show available MIDI dervices",action="store_true")
parser.add_argument("-c","--comports", help="show COM ports",action="store_true")
parser.add_argument("-v","--verbose", help="increase output verbosity",action="store_true")
args = parser.parse_args()
##########################################

# init ini file parser
# allow_no_value=True -> to allow adding comments without value, so no trailing =
Config = configparser.ConfigParser(allow_no_value=True)


# use start option to set debug infos, like MIDI commands generated, CAT dialog, etc...
if args.verbose:
    DEBUG = True
else:
    DEBUG=False

#DEBUG=True # to force the debugging

def ReadIniFile():
########################################
# Read the ini file and get settings
#
# some datas are INT so need to be converted with .getint !
########################################
    try:
        # read ini file
        Config.read('midi2ts590.ini')

        # check if Midi section exists
        if Config.has_section('Midi'):
            config.MidiDeviceIn = Config.getint('Midi','deviceIN')     # get the device Midi IN, reads and converts in INT
            config.MidiDeviceOut = Config.getint('Midi','deviceOUT')   # get the device Midi OUT
        else:
            input("Midi section missing in config file. Please correct this !\nCTRL-C to exit")
            sys.exit(1)

        # check if default section exists
        if Config.has_section('Default'):
            config.RadioMode = Config.get('Default','mode')
            config.RadioVFO = Config.get('Default','VFO')
            config.RadioTuningStep = Config.getint('Default','tuningstep')
            #config.RadioPoll = Config.getint('Default','radiopoll')
            config.RadioSniff = Config.getint('Default','radiosniff')
        else:
            input("Default section missing in config file. Please correct this !\nCTRL-C to exit")
            sys.exit(1)

        # check if Radio section exists
        if Config.has_section('Radio'):
            config.RadioModel=Config.get('Radio','model')
            config.RadioPort=Config.get('Radio','comport')
            config.RadioBaudrate=Config.getint('Radio','baudrate')     #reads and converts in INT
            config.RadioBytesize=Config.getint('Radio','bytesize')
            config.RadioStop=Config.getint('Radio','stopbits')
            config.RadioParity=Config.get('Radio','parity')
            config.RadioXonXoff=Config.getint('Radio','xonxoff')
            config.RadioRtsCts=Config.getint('Radio','rtscts')
            config.RadioDsrDtr=Config.getint('Radio','dsrdtr')
            config.polltime=Config.getint('Radio','polltime')
            config.RadioRxtimeout=Config.getint('Radio','rxtimeout')
            config.RadioTxtimeout=Config.getint('Radio','txtimeout')

        else:
            input("Radio section missing in config file. Please correct this !\nCTRL-C to exit")
            sys.exit(1)

        # check if Commands section exists
        if Config.has_section('Commands'):
            config.Radiocmd1 = Config.get('Commands','cmd1')
            config.Radiocmd2 = Config.get('Commands','cmd2')
            config.Radiocmd3 = Config.get('Commands','cmd3')
            #pass # do nothing
        else:
            input("Commands section missing in config file. Please correct this !\nCTRL-C to exit")
            sys.exit(1)

    # if an option is missing, raise an error
    except configparser.NoOptionError:
        input ("Missing option(s) in config file !\nPlease correct this or remove file to allow creating a default one !")
        sys.exit(1)
    else:   # otherwise, we're happy
        print ("Config file correctly read & parsed\n")


def CreateIniFile():
########################################
# create_midi2ts590_inifile
# in case the ini file does not exist, create one with default values
########################################
    inifile = open('midi2ts590.ini','w')

    # add default section
    Config.add_section('Default')
    Config.set('Default','# midi2ts590 config file')
    Config.set('Default','# defaults values created by program')
    Config.set('Default','# See manual for help in setting')
    Config.set('Default','mode','USB')
    Config.set('Default','VFO','A')
    Config.set('Default','tuningstep','5')
    #Config.set('Default','radiopoll','0')
    Config.set('Default','radiosniff','0')
    # add section Midi
    Config.add_section('Midi')
    # add settings
    Config.set('Midi','deviceIN','1')
    Config.set('Midi','deviceOUT','3')

     # add section Radio
    Config.add_section('Radio')
    # add settings
    Config.set('Radio','model','TS590s')
    Config.set('Radio','comport','COM33')
    Config.set('Radio','baudrate','57600')
    Config.set('Radio','bytesize','8')
    Config.set('Radio','stopbits','1')
    Config.set('Radio','parity','N')
    Config.set('Radio','xonxoff','0')
    Config.set('Radio','rtscts','0')
    Config.set('Radio','dsrdtr','0')
    Config.set('Radio','polltime','1000')
    Config.set('Radio','rxtimeout','100')
    Config.set('Radio','txtimeout','100')

    # add section Commands
    Config.add_section('Commands')
    # add settings
    Config.set('Commands','# put one or more KENWOOD commands (see manual) on each following line')
    Config.set('Commands','# e.g cmd1 = VV;VX0;         set VFO A=B and VOX OFF')
    Config.set('Commands','# e.g cmd2 = rt0;            will put RIT OFF')
    Config.set('Commands','# these commands will be sent at startup')
    Config.set('Commands','cmd1','VV')
    Config.set('Commands','cmd2','')
    Config.set('Commands','cmd3','')

    # and lets write it out...
    Config.write(inifile)
    inifile.close()

    # now read the config file
    ReadIniFile()


def ChangeMode(mode:str,ledonly = False):
################################
# change mode on radio and lights led under button
#
# input:    mode:str must be 'CW', 'USB', 'LSB', 'FSK'
#           ledonly:bool if we ONLY want to change the LED status NOT sending to radio
#           by default ledonly False
################################
    #global RadioMode
    if mode == 'CW':
        config.RadioMode = 'CW'
        strCat = 'MD3'     # MODE = CW
        # switch on backlight
        Midi_Out.write([ [[144,49,127],0], [[144,50,0],0], [[144,51,0],0] , [[144,52,0],0] ])
    elif mode == 'LSB':
        config.RadioMode = 'LSB'
        strCat = 'MD1'
        # switch on backlight
        Midi_Out.write([ [[144,49,0],0] , [[144,50,0],0] , [[144,51,0],0] , [[144,52,127],0] ])
    elif mode == 'USB':
        config.RadioMode = 'USB'
        strCat = 'MD2'
        # switch on backlight
        Midi_Out.write([ [[144,49,0],0] , [[144,50,0],0] , [[144,51,127],0] , [[144,52,0],0] ])
    elif mode == 'FSK':
        config.RadioMode = 'FSK'
        strCat = 'MD6'
        # switch on backlight
        Midi_Out.write([ [[144,49,0],0] , [[144,50,127],0] , [[144,51,0],0] , [[144,52,0],0] ])
    if ledonly == False:                    # if we only want to change the Leds and not send to radio
        ts590.query(strCat,0)


def ChangeVFO(vfo:str,ledonly=False):
########################################
# put radio on VFO A or B
#
# input vfo:str must be 'A' or 'B'
########################################
    if vfo == 'A':
        strCat='FR0'
        config.RadioVFO = 'A'
        # switch on backlights
        Midi_Out.write([ [[144,35,127],0] , [[144,34,0],0] , [[144,3,0],0] , [[144,4,0],0] ])
    elif vfo == 'B':
        config.RadioVFO = 'B'
        strCat='FR1'
        # switch on backlights
        Midi_Out.write([[[144,34,127],0] , [[144,35,0],0] , [[144,3,0],0] , [[144,4,0],0] ])
    if ledonly == False:
        ts590.query(strCat,0)


def DJ_init():
##################
# init pygame
##################
    pygame.midi.init()
def DJ_count()->int:
#############################################
# count the number of Midi devices connected
#############################################
    MidiDeviceCount = pygame.midi.get_count()
    print ("Number of Midi devices found =",MidiDeviceCount)
    return MidiDeviceCount
def DJ_info():
#############################################
# lists all Midi deveices
#############################################
    print("List of all available MIDI devices")
    for i in range(pygame.midi.get_count()):
        r = pygame.midi.get_device_info(i)
        (interf, name, input, output, opened) = r

        in_out = ""
        if input:
            in_out = "input"
        if output:
            in_out = "output"

        # make a nice table of this
        #print("%2i: interface :%s:, name :%s:, opened :%s:  %s" % (i, interf, name, opened, in_out))
        print ('nr: {: <3}Interface: {: <10} Name: {: <30}   {: <8} Opened:{}'.format(i, str(interf,'UTF-8'), str(name,'UTF-8'), in_out, opened))

def DJ_initInput(device:int)->bool:
# check if the selected input device is correct
    info = pygame.midi.get_device_info(device)     # get infos about input device, returns (interf, name, input, output, opened)
    #print (info)
    #print (info[0])
    if info == None:        # if out of range, pygame class returns None
        DJ_info()           #show list of available devices
        input("MIDI device number out of range\nCTRLC-C and correct this")
        sys.exit(1)
    elif info[4] == 1:      # "opened" var in tuple returned, if 1 then device opened
        DJ_info()
        input ("Selected MIDI device already in use !\nCTRLC-C and correct this")
        sys.exit(1)
    elif info[2] != 1:      # "input" var in tuple returned, if 1 then device is an input
        DJ_info()
        print("Selected device nr",device)
        input ("This MIDI device is not an input !\nCTRLC-C and correct this")
        sys.exit(1)
    else:
        if DEBUG:
            print("MIDI input initialized",device)
        return True

def DJ_initOutput(device:int)->bool:
# check if the selected output device is correct, same tests as above
    info = pygame.midi.get_device_info(device)
    #print (info)
    if info == None:
        DJ_info()
        input("Device number out of range !\nCTRLC-C and correct this")
        sys.exit(1)
    elif info[4] == 1:
        DJ_info()
        input ("Selected MIDI device already in use !\nCTRLC-C and correct this")
        sys.exit(1)
    elif info[3] != 1:
        DJ_info()
        print("Selected device nr",device)
        input("This MIDI device is not an output !\nCTRLC-C and correct this ")
        sys.exit(1)
    else:
        if DEBUG:
            print("MIDI output initialized",device)
        return True

def DJ_LedsON():
    Midi_Out.write([ [[144,1,127],0], [[144,2,127],0], [[144,3,127],0] , [[144,4,127],0] , [[144,33,127],0], [[144,34,127],0], [[144,35,127],0] , [[144,49,127],0], [[144,50,127],0], [[144,51,127],0] , [[144,52,127],0] , [[144,81,127],0], [[144,82,127],0], [[144,83,127],0] , [[144,43,127],0] , [[144,45,127],0] , [[144,48,127],0] ])
def DJ_LedsOFF():
    Midi_Out.write([ [[144,1,0],0], [[144,2,0],0], [[144,3,0],0] , [[144,4,0],0] , [[144,33,0],0], [[144,34,0],0], [[144,35,0],0] , [[144,49,0],0], [[144,50,0],0], [[144,51,0],0] , [[144,52,0],0] , [[144,81,0],0], [[144,82,0],0], [[144,83,0],0] , [[144,43,0],0] , [[144,45,0],0] , [[144,48,0],0] ])
def DJ_LedsBlink(numTimes,period):
    for i in range(0,numTimes):     ## Run loop numTimes
        DJ_LedsON()
        time.sleep(period)
        DJ_LedsOFF()
        time.sleep(period)
def DJ_LedRECORD(state:int):
    Midi_Out.write([[[0x90,0x2B,state],0]])
def DJ_LedAUTO(state:int):
    MidiOut.write([[[0x90,0x2D,state],0]])
def DJ_LedDA_SYNC(state:int):
    Midi_Out.write([[[0x90,0x23,state],0]])
def DJ_LedDA_CUE(state:int):
    Midi_Out.write([[[0x90,0x22,state],0]])
def DJ_LedDA_PLAY(state:int):
    Midi_Out.write([[[0x90,0x21,state],0]])
def DJ_LedDA_KP1(state:int):
    Midi_Out.write([[[0x90,0x01,state],0]])
def DJ_LedDA_KP2(state:int):
    Midi_Out.write([[[0x90,0x02,state],0]])
def DJ_LedDA_KP3(state:int):
    Midi_Out.write([[[0x90,0x03,state],0]])
def DJ_LedDA_KP4(state:int):
    Midi_Out.write([[[0x90,0x04,state],0]])
def DJ_LedDB_SYNC(state:int):
    Midi_Out.write([[[0x90,0x53,state],0]])
def DJ_LedDB_CUE(state:int):
    Midi_Out.write([[[0x90,0x52,state],0]])
def DJ_LedDB_PLAY(state:int):
    Midi_Out.write([[[0x90,0x51,state],0]])
def DJ_LedMODE(state:int):
    Midi_Out.write([[[0x90,0x30,state],0]])
def DJ_LedDB_KP1(state:int):
    Midi_Out.write([[[0x90,0x31,state],0]])
def DJ_LedDB_KP2(state:int):
    Midi_Out.write([[[0x90,0x32,state],0]])
def DJ_LedDB_KP3(state:int):
    Midi_Out.write([[[0x90,0x33,state],0]])
def DJ_LedDB_KP4(state:int):
    Midi_Out.write([[[0x90,0x34,state],0]])


def DJ_scan():
        event = Midi_In.read(10)[0]
        data = event[0]
        device = data[0]
        status = data[1]
        control = data[2]
        value = data[3]
        timestamp = event[1]

        if DEBUG:
            print ("Device:",device,"Status",status,"Control",control,"Value:",value,timestamp)

        #detect rotation of jogs and pots
        if device == 0xB0:                              # a pot/slider/jog has been turned
            if status == 48:                            # JOG A activity detected
                if DEBUG:
                    print("JOG_A turned")
                if control < 64:
                    ts590.VFOfreq(0,0,config.RadioTuningStep)
                else:
                    ts590.VFOfreq(0,1,config.RadioTuningStep)
            elif status == 49:                          # JOG B activity detected
                if DEBUG:
                    print("JOG_B turned")
                if control < 64:                        # turned CW
                    ts590.RITUp()                       # send RIT up
                else :                                  # turned CCW
                    ts590.RITDown()                     # send RIT down
            elif status == 54:                          # SLIDER activity detected
                if DEBUG:
                    print(control*2)
                strCat = format ("AG%04d"% ( control *2  ))     # slider value is 0-127, RX VOLUME needs 0-255
                ts590.query(strCat,0)                           # send to radio

            elif status == 59 and config.RadioMode != 'CW' and config.RadioMode != 'FSK':     # if DA_MEDIUM pot moved change SL command but NOT in CW
                global oldsl
                sl = math.floor(( control / 9.5))       # to get values from 0-13
                if DEBUG:
                    print ("SL:",sl)                    # SL command 00-11
                if sl != oldsl:                         # if the new value SL is different from previous one
                    strCat = format ("SL%02d"%sl)       # format de CAT string
                    oldsl = sl                          # set the old value of SL
                    ts590.query(strCat,0)               # send CAT command

            elif status == 60 and config.RadioMode =='CW':              # CW bandwidth 050-2500
                global oldfwcw
                fwcwval =[50,80,100,150,200,250,300,400,500,600,1000,1500,2000,2500]    # these are the values for FW command is CW
                fwcw = math.floor(control / 9.5)                                      # to get values from 0-13
                if fwcw != oldfwcw:
                    strCat = format ("FW%04d"% fwcwval[fwcw])
                    ts590.query(strCat,0)
                    oldfwcw = fwcw
                if DEBUG:
                    print("CW FW:",strCat)

            elif status == 60 and config.RadioMode =='FSK':         #FSK bandwith 250-1500
                global oldfwfsk
                fwfskval = [250,500,1000,1500]                      # values for FW in FSK
                fwfsk = math.floor(control / 41)
                if fwfsk != oldfwfsk:
                    strCat= format ("FW%04d"% fwfskval[fwfsk])
                    ts590.query(strCat,0)
                    oldfwfsk = fwfsk
                if DEBUG:
                    print("FSK FW:",strCat)

            elif status == 63 and config.RadioMode != 'CW' and config.RadioMode != 'FSK':
                global oldsh
                sh = math.floor(control / 9.5)                     # SH command 00-13
                if sh != oldsh:
                    strCat = format ("SH%02d"% sh)
                    ts590.query(strCat,0)
                    oldsh = sh
                if DEBUG:
                    print("SH:",sh)


            elif status == 64 and config.RadioMode =='CW':              # CW only shift command IS
                global oldis
                istab =[300,350,400,450,500,550,600,650,700,750,800,850,900,950,1000] # IS values for CW
                isval = math.floor(control/8.5)
                if isval != oldis:
                    strCat = format ("IS %04d"%istab[isval])
                    ts590.query(strCat,0)
                    oldis = isval
                if DEBUG:
                    print ("IS:",isval)

            elif status == 57:                                          # sets the power 005-100
                out = math.floor(5 + (100 - 5) * control / 127 )
                if DEBUG:
                    print ("%03d"%out)
                strCat = format ("PC%03d"% out)
                ts590.query(strCat,0)
            elif status == 61:                                          #
                if DEBUG:
                    pass

        ## check if buttonss have been pressed
        if device == 144:                               # a key has been pressed
            if status == 1 and control == 127:          # DA_KP1 button pressed
                if DEBUG:
                    print("DA_KP1")
                ts590.query('TS1',0)                    # send TF-SET ON
                DJ_LedDA_KP1(1)                         # light corresponding LED
            elif status == 1 and control == 0:          # if ket is released
                if DEBUG:
                    print('DA_KP1 released')
                ts590.query('TS0',0)                    # TF-SET OFF
                DJ_LedDA_KP1(0)                         # LED off
            elif status == 2:                           # DA_KP2 pressed
                if control == 127 and config.RadioMode == 'CW':
                    if DEBUG:
                        print('DA_KP2 pressed')
                    ts590.query('CA1',0)                # CW TUNE ON
                    DJ_LedDA_KP2(1)
                else:
                    ts590.query('CA0',0)                # CW TUNE OFF
                    DJ_LedDA_KP2(0)
            elif status == 3:                             # DA_KP3 pressed
                if control == 127:
                    if DEBUG:
                        print('DA_KP3 pressed')
                    ts590.query('FR0;FT1',0)            # SPLIT A/B
                    DJ_LedDA_KP3(1)                     # LED on
                    DJ_LedDA_KP4(0)                     # all other mode LEDs off
                    DJ_LedDA_SYNC(0)
                    DJ_LedDA_CUE(0)
            elif status == 4:                           #DA_KP4 pressed
                if control == 127:
                    if DEBUG:
                        print('DA_KP3 pressed')
                    ts590.query('FR1;FT0',0)            #SPLIT B/A
                    DJ_LedDA_KP3(0)                     # LED off
                    DJ_LedDA_KP4(1)                     # LED on
                    DJ_LedDA_SYNC(0)                    # LED VFO A off
                    DJ_LedDA_CUE(0)                     # LED VFO B off
            elif status == 33:                          #VFO A=B
                if control == 127:
                    if DEBUG:
                        print('DA_PLAY pressed')
                    ts590.query('VV',0)                 # send VV command
                    DJ_LedDA_PLAY(1)
                else:
                    DJ_LedDA_PLAY(0)
            elif status == 34:                          # DA_CUE key presses
                if control == 127:
                    if DEBUG:
                        print('DA_CUE pressed')
                    ChangeVFO('B')
                    """
                    ts590.query('FR1',0)                # VFO A FR command
                    DJ_LedDA_SYNC(0)
                    DJ_LedDA_CUE(1)                     #DE_CUE LED on
                    DJ_LedDA_KP3(0)                     # LED off
                    DJ_LedDA_KP4(0)                     # LED off
                    """
            elif status == 35:                            # DA_SYNC presses
                if control == 127:
                    if DEBUG:
                        print('DA_SYNC pressed')
                    ChangeVFO('A')
                    """
                    ts590.query('FR0',0)                # VFO B FR command
                    DJ_LedDA_SYNC(1)
                    DJ_LedDA_CUE(0)
                    DJ_LedDA_KP3(0)
                    DJ_LedDA_KP4(0)
                    """
            elif status == 43:                            # REC button
                if control == 127:                      # pressed
                    if DEBUG:
                        print('REC pressed RadioIsON :',config.RadioIsON)
                    if config.RadioIsON == 1:           # is the radio ON flag
                        ts590.RadioOnOff(0)             # switch radio off
                        DJ_LedRECORD(0)                 # REC LED off
                        config.RadioIsON = 0            # swap flag
                    else:                               # radio is off
                        ts590.RadioOnOff(1)             # turn it on
                        DJ_LedRECORD(1)
                        config.RadioIsON = 1
            elif status == 49:                            # DA_KP1 button
                if control == 127:                      # pressed
                    if DEBUG:
                        print('DB_KP1 pressed')
                    ChangeMode('CW')                    # change mode to CW
            elif status == 50:                            # DA_KP2 button
                if control == 127:                      # pressed
                    if DEBUG:
                        print('DB_KP2 pressed')
                    ChangeMode('FSK')                   # FSK mode
            elif status == 51:                            # DA_KP3 presses
                if control == 127:
                    if DEBUG:
                        print('DB_KP3 pressed')
                    ChangeMode('USB')                   # USB
            elif status == 52:                            # DA_KP4
                if control == 127:
                    if DEBUG:
                        print('DB_KP4 pressed')
                    ChangeMode('LSB')                   # LSB
            elif status == 83:                            # DB_SYN pressed
                if control == 127:
                    if DEBUG:
                        print('DB_SYNC pressed')
                    if config.RITisON == 0:             # RIT ON/OFF toggle
                        ts590.query('RT1',0)            # RT command
                        DJ_LedDB_SYNC(1)
                        config.RITisON = 1
                    elif config.RITisON == 1:
                        ts590.query('RT0',0)
                        DJ_LedDB_SYNC(0)
                        config.RITisON = 0
            elif status == 82:                            # DB_CUE pressed
                if control == 127:
                    if DEBUG:
                        print('DB_CUE pressed')
                    if config.XITisON == 0:             #  XIT toggle
                        ts590.query('XT1',0)
                        DJ_LedDB_CUE(1)
                        config.XITisON = 1
                    elif config.XITisON == 1:
                        ts590.query('XT0',0)
                        DJ_LedDB_CUE(0)
                        config.XITisON = 0
            elif status == 81:                            # DB_PLAY pressed
                if control == 127:
                    if DEBUG:
                        print('DB_PLAY pressed')
                    ts590.query('RC',0)                 # RC command RIT clear
                    DJ_LedDB_PLAY(1)
                else:
                    DJ_LedDB_PLAY(0)

            ## add here more functions if needed


def CheckRadioState():
#####################################
# TEST to check the radio state periodically
# if some changes are detected
# change the LEDs and flags accordingly
#
# some glitches due to state difference between polling time
# needs some work
#####################################
    answerIF = ts590.query('IF',37)                 # read radio IF frame
    if answerIF != None:                            # if we have a valid answer
        mode = ts590.ReadCmdIF(answerIF)[5]         # extract the mode
        split = ts590.ReadCmdIF(answerIF)[7]        # extract split
        VFO = ts590.ReadCmdIF(answerIF)[6]          # extract VFO

        if DEBUG:
            print("\nVariables in CheckRadioState:")
            print(time.ctime())                     # print time for checking
            print("split:",split)
            print ("VFO:",VFO)
            print("Mode:",mode)

        if 1<= int(mode) <= 9:                      #if we have a valid mode
            modeStr = ts590.ConvertMode(int(mode))  # convert it to readable string
            ChangeMode(modeStr,1)

        # check VFO states
        if split == '0':                            # split off
            if VFO == '0':                          # if VFO A main
                ChangeVFO('A',1)
            elif VFO == '1':
                ChangeVFO('B',1)
        if split == '1':            # split on
            if VFO == '0':           # VFO A is main
                DJ_LedDA_KP3(1)                     # LED off
                DJ_LedDA_KP4(0)                     # LED on
                DJ_LedDA_SYNC(0)                    # LED VFO A off
                DJ_LedDA_CUE(0)                     # LED VFO B off
                config.radioVFO ='A'
            else:
                DJ_LedDA_KP3(0)                     # LED off
                DJ_LedDA_KP4(1)                     # LED on
                DJ_LedDA_SYNC(0)                    # LED VFO A off
                DJ_LedDA_CUE(0)                     # LED VFO B off
                config.radioVFO ='B'
    else:
        pass


def MakeDJequalRadio(rcvdatas):
#####################################
# Check the datas on the COM port between the radio and logging software
# if an answer to IF request is found, (most logging software rely on this)
# check if it is complete and change the LEDs on console and flags accordingly
#
# some glitches due to state difference between polling time
# may need some work 23/01/2023
#####################################
    try:
        start = rcvdatas.find("IF")                     # find the start of an IF in the received frame
        if start != -1 and rcvdatas[start+37] == ";":   # if found (!=1) and if at position 37 we've a ; separator
            rcvdatas = rcvdatas[start:start+37]         # we extract the IF frame
            answerIF = ts590.ReadCmdIF(rcvdatas)        # we extract all infos from the above frame

            split = answerIF[7]                         # extract split
            VFO = answerIF[6]                           # extract VFO
            mode = answerIF[5]                          # extract the mode
            modeStr = ts590.ConvertMode(int(mode))      # convert to readable mode

            if DEBUG:
                print("\nvariables in MakeDJequalRadio:")
                print("rcvdatas:",rcvdatas)
                print("split:",split,type(split))
                print ("VFO:",VFO,type(VFO))
                print("Mode:",mode,type(mode))
                print("ModeStr:",modeStr,type(modeStr))
                print("RadioMode",config.RadioMode,type(config.RadioMode))
                print("RadioVFO",config.RadioVFO,type(config.RadioVFO))

            #if 1<= int(mode) <= 9:                      #if we have a valid mode
            if modeStr != config.RadioMode:
                mode = ts590.ConvertMode(int(mode))  # convert it to readable string
                ChangeMode(modeStr,0)                   # change only Leds, no CAT


            # check VFO states
            if split == '0':                            # split off
                if VFO == '0':                          # if VFO A main
                    ChangeVFO('A',1)

                elif VFO == '1':
                    ChangeVFO('B',1)

            if split == '1':            # split on
                if VFO == '0':           # VFO A is main
                    DJ_LedDA_KP3(1)                     # LED off
                    DJ_LedDA_KP4(0)                     # LED on
                    DJ_LedDA_SYNC(0)                    # LED VFO A off
                    DJ_LedDA_CUE(0)                     # LED VFO B off
                    config.RadioVFO = 'A'
                else:
                    DJ_LedDA_KP3(0)                     # LED off
                    DJ_LedDA_KP4(1)                     # LED on
                    DJ_LedDA_SYNC(0)                    # LED VFO A off
                    DJ_LedDA_CUE(0)                     # LED VFO B off
                    config.RadioVFO = 'B'
        else:
            pass
    except:
        print('Exception in MakeDJequalRadio')

def pollRadio(polltime):
# check periodically the radio state
    global stop_thread                                          # set a flag global variable needed to stop the thread
    while True:
        try:
            time.sleep(polltime/1000)               # to poll is ms set in config file
            if DEBUG:
                print("\nVariables in pollRadio:")
                print(time.ctime())                     # print time for checking
                print("polltime:",config.polltime)
            CheckRadioState()
            if stop_thread:                         # if the flag is set and thread join
                break                               # stop thread
        except:
            print("Exception in Pollradio thread")
            pass


def SniffRadio(polltime):
    global stop_thread                                          # set a flag global variable needed to stop the thread
    while True:
        try:
            if DEBUG:
                print("\nVariables in pollRadio:")
                print(time.ctime())                     # print time for checking
                print("polltime:",config.polltime)
            time.sleep(polltime/1000)               # to poll is ms set in config file
            rcvdatas = ts590.read()
            MakeDJequalRadio(rcvdatas)
            if stop_thread:                         # if the flag is set and thread join
                break                               # stop thread

        except:
            print("Exception in SniffRadio thread")
            pass


###################################################
## MAIN
##
## reads configuration file or create it if not exist
## creates a connection to TS590 with the Kenwood library
## inits the DJcontroller and creates in/out objects
## polls the DJcontroller and sends command to TS590
###################################################
if __name__ == '__main__':
    print ("\n%s - (c) Patrick EGLOFF aka TK5EP" %(__Title))
    print ("Version %s  date:%s\n" % (__Version, __VersionDate))

    inifile = 'midi2ts590.ini'                              # check if ini file exists and read the settings
    if os.path.isfile(inifile):
        ReadIniFile()
    else:
        print('\nConfiguration file does not exist !\nCreating it in a few seconds, then edit it to your needs if something goes wrong.\n')
        time.sleep(5)
        CreateIniFile()                                     # if not, create it

    ts590 = KwdCat()                                        # create instance of KwdCat the Kenwood CAT library

    DJ_init()                                               # init
    if args.midi:                                           # if optional -m or --midi argument at startup
        DJ_info()                                           # lists all available MIDI devices

    if args.comports:                                          # show list of COM ports if asked as option at startup
        ts590.find_ports()

    if (ts590.open_port(port=config.RadioPort)):            # opening port with default values
    # test with all parameters set with config file values
    #if (ts590.open_port(port=config.RadioPort,baudrate=config.RadioBaudrate,bytesize=config.RadioBytesize,stopbits=config.RadioStopbits,xonxoff=config.RadioXonXoff,rtscts=config.RadioRtsCts,dsrdtr=config.RadioDsrDtr,parity=config.RadioParity,rts=config.RadioRts,dtr=config.RadioDtr,timeout=config.RadioRxtimeout)):
        print ('Radio model :',config.RadioModel,'on',ts590.serial.port)
        print ('Baudrate=',ts590.serial.baudrate,'Bits=',ts590.serial.bytesize,'Stop=',ts590.serial.stopbits,'Parity=',ts590.serial.parity)
        print ("Flow controls: XOn/XOff=",ts590.serial.xonxoff,"RTS/CTS=",ts590.serial.rtscts,"DSR/DTR=",ts590.serial.dsrdtr)
        print ("Lines: RTS=",ts590.serial.rts,"DTR=",ts590.serial.dtr,"CTS=",ts590.serial.cts,"DSR=",ts590.serial.dsr,"Timeout=",ts590.serial.timeout,"\n")
    else:
        print(config.RadioPort,"not available, busy or bad setting !")
        print("Below are available ports, set one in the configuration file")
        ts590.find_ports()                                  # show a list of found comports
        input('\nStopping. CTRL-C to stop')
        sys.exit()

    if (ts590.checkradio()):                                # check is radio is answering
        print ("Radio communication OK\n")
    else:                                                   # if no answer
        ts590.close_port()                                  # close port
        input('\nCTRL-C to EXIT')
        sys.exit(0)



    if DJ_initInput(config.MidiDeviceIn):                   # check if device is input, not busy
        Midi_In = pygame.midi.Input(config.MidiDeviceIn)    # open Midi input device
        print('MIDI input device ready')
    if DJ_initOutput(config.MidiDeviceOut):                 # check output device
        Midi_Out = pygame.midi.Output(config.MidiDeviceOut) # open Midi output device
        print('MIDI output device ready')
    DJ_LedsBlink(3,0.3)                                     # some fancy animation

    ts590.query('PS1',0)                                    # send radio ON
    config.RadioIsON = 1                                    # flag for radio ON/OFF state
    DJ_LedRECORD(1)                                         # switch LED ON

    ChangeMode(config.RadioMode)                            # switch radio to default mode
    ChangeVFO(config.RadioVFO)                              # put radio to default VFO
    if config.Radiocmd1:                                    # if the cmd1 is set in configuration file
        ts590.query(config.Radiocmd1,0)                     # send to radio, 0 means no echo from radio needed
    if config.Radiocmd2:
        ts590.query(config.Radiocmd2,0)
    if config.Radiocmd3:
        ts590.query(config.Radiocmd3,0)

    # inits for a little animation
    animation = "|/-\\"                                     # like a turning wheel
    anicount = 0                                            # init animation counter position

    print("\nFor a 'clean' stop of this software, use CTRL-C.")

    if config.RadioSniff == 1:
        polling_daemon = Thread(target=pollRadio, args=(
        config.polltime,), daemon=True, name='Poll Radio')      # create a thread for the radio polling
        polling_daemon.start()                                          # start the thread
        stop_thread = False                                     #flag to stop the thread by calling it with join()

    if config.RadioSniff == 2:
        sniffer_daemon = Thread(target=SniffRadio, args=(
        config.polltime,), daemon=True, name='Sniff Radio')      # create a thread for the radio polling
        sniffer_daemon.start()                                          # start the thread
        stop_thread = False                                     #flag to stop the thread by calling it with join()


    #############################
    # MAIN loop
    #############################
    while True:
        try:
            #print ("type",type(IFmode))
            #ts590.query('AI0',3)

            #ts590.query('FV',6)

            #answerVV = ts590.query('VV',13)
            #print(answerVV)

            #answerFA = ts590.query('FA',13)
            #print(ts590.ReadCmdFAFB(answerFA))

            #xianswer=ts590.query('XI',17)
            #print(ts590.ReadCmdXI(xianswer))

            #print(ts590.ConvertMode(3))

            #print(config.runningMode)                              # this is mode set on radio
            #print(config.RadioMode)                         # this is mode set by sw


            if Midi_In.poll():                                      # check if something is present on the MIDI input device
                DJ_scan()                                           # if yes check what it is
                print(animation[anicount],end='\r')                 # show activity with a small animation at each midi device poll
                anicount = (anicount + 1)%4                         # next animation position, reset the number at 4 to avoid overflow


        except KeyboardInterrupt:                                   # if we press CTRL-C to interrupt the program
            if config.RadioSniff == 1:
                stop_thread = True                                      # set the flag to kill the thread
                polling_daemon.join()                                           # join the thread to stop it
            if config.RadioSniff == 2:
                stop_thread = True                                      # set the flag to kill the thread
                sniffer_daemon.join()                                           # join the thread to stop it
            ts590.close_port()                                      # close radio port
            print('All threads killed, exiting in 2s')
            time.sleep(2)

            sys.exit()


