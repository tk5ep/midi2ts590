# midi2ts590 by Patrick EGLOFF aka TK5EP
#
#
# reads MIDI commands from a HERCULES DJcontrol compact controller
# each JOG, slider or button have a function assigned and sends KENWOOD remote commands to a TS590s via a COM port
# MIDI command are including the device number (0 to 4, depending on your setup), the MIDI status (depending on the kind of control), the control ID (depending on the device) and finally the control value
#
# v 0.1 started 15/02/17
# v 0.2 15/01/2023

Name = "Remote control for TS590 with DJcontrol Compact"
Version = "0.2"
VersionDate = "15/01/2023"


# import libraries
import configparser                         #https://docs.python.org/3/library/configparser.html
import os
import sys
import math
import serial                               #https://pythonhosted.org/pyserial/
from serial import SerialException
from serial.tools.list_ports import comports
from time import sleep
from os import environ                      # following 2 lines are to hide pygame welcome message
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame.midi                          #http://www.pygame.org/docs/ref/midi.html

# global variables from a config file
import config

# init ini file parser
Config = configparser.ConfigParser()
#Config = configparser.ConfigParser(allow_no_value=True) #  allow_no_value=True -> to allow adding comments without value, so no trailing =

########################################
# Read the ini file and get settings
# datas are strings so need to be converted with .getxxx !
########################################
def ReadIniFile():
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
            config.RadioDefaultMode = Config.get('Default','mode')
            config.RadioDefaultVFO = Config.get('Default','VFO')
        else:
            input("Default section missing in config file. Please correct this !\nCTRL-C to exit")
            sys.exit(1)

        # check if Radio section exists
        if Config.has_section('Radio'):
            config.RadioModel=Config.get('Radio','model')
            config.RadioPort=Config.get('Radio','comport')
            config.RadioSpeed=Config.getint('Radio','speed')     #reads and converts in INT
            config.RadioBits=Config.getint('Radio','bits')
            config.RadioStop=Config.getint('Radio','stop')
            config.RadioParity=Config.get('Radio','parity')
            config.RadioXonXoff=Config.getint('Radio','xonxoff')
            config.RadioRtsCts=Config.getint('Radio','rtscts')
            config.RadioDsrDtr=Config.getint('Radio','dsrdtr')

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


########################################
# create_midi2ts590_inifile
# in case the ini file does not exist, create one with default values
########################################
def CreateIniFile():
    inifile = open("midi2ts590.ini",'w')

    # add default section
    Config.add_section('Default')
    Config.set('Default','# midi2ts590 config file')
    Config.set('Default','# defaults values created by program')
    Config.set('Default','mode','USB')
    Config.set('Default','VFO','A')
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
    Config.set('Radio','speed','57600')
    Config.set('Radio','bits','8')
    Config.set('Radio','stop','1')
    Config.set('Radio','parity','N')
    Config.set('Radio','xonxoff','0')
    Config.set('Radio','rtscts','0')
    Config.set('Radio','dsrdtr','0')

    # add section Commands
    Config.add_section('Commands')
    # add settings
    Config.set('Commands','# put one or more KENWOOD commands (see manual) on each following line')
    Config.set('Commands','# e.g cmd1 = VV;VX0;         set VFO A=B and VOX OFF')
    Config.set('Commands','# e.g cmd2 = rt0;            will put RIT OFF')
    Config.set('Commands','# these commands will be sent at startup')
    Config.set('Commands','cmd1','')
    Config.set('Commands','cmd2','')
    Config.set('Commands','cmd3','')

    # and lets write it out...
    Config.write(inifile)
    inifile.close()

    # now read the config file
    ReadIniFile()

#####################################
# class to handle the com port and radio
#####################################
class SerialCom(object):
    def open_comport(self) -> bool:
        # define the serial port for radio
        try:
            print("Opening COM port...")

            self.serial = serial.Serial(        # set the port parameters
            port = config.RadioPort,
            baudrate = config.RadioSpeed,
            bytesize = config.RadioBits,
            stopbits = config.RadioStop,
            parity = config.RadioParity,
            xonxoff = config.RadioXonXoff,      #software flow control
            rtscts = config.RadioRtsCts,        #hardware (RTS/CTS) flow control
            dsrdtr = config.RadioDsrDtr,        #hardware (DSR/DTR) flow control
            timeout = 0)                        #needed !

            # setting RTS & DTR lines
            self.serial.dtr = config.RadioDtr
            self.serial.rts = config.RadioRts

            self.serial.is_open             # open COM port
            return True
        except SerialException:             # if COM port communication problem
            return False


    def find_comports(self):
    ########################################
    # show a list of current COM ports
    ########################################
        sys.stderr.write('\nBEWARE, some virtual ports may not be shown !\n')
        ports = []
        for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
            sys.stderr.write('{:2}: {:20} {!r}\n'.format(n, port, desc))
            ports.append(port)


    def close_comport(self) -> bool:
        #################################
        # Close the comport
        #################################
        try:
            self.serial.close()
        except AttributeError:
            print("open_comport has not been called yet!")
            return False
        else:
            print("Closing the COM port...")
            return True


    def GetDataFromRadio(self) -> str:
        ########################################
        # read datas from radio
        ########################################
        received_data = self.serial.read_until(';')    # read serial port until we get a ; separator
        data_left = self.serial.inWaiting()            # check for remaining bytes
        received_data += self.serial.read(data_left)   # add remaining datas to buffer
        config.received_datas = (received_data.decode())   # decode in ASCII
        #print (received_datas)
        return config.received_datas


    def SendDataToRadio(self,datastosend:str):
        ######################################
        # Write strings to comport
        ######################################
        if self.serial.is_open:
            try:
                #_send_data = input(_t1 + " (TX) >> ")
                #self.serial.write(_send_data.encode())
                self.serial.write(datastosend.encode())
            except SerialException:
                print('Disconnected while writing')
                self.close_comport()


    def CheckRadio(self) -> bool:
        #################################################
        # Check if RadioPort is open and Radio is ON
        #################################################
        print ('Listening the COM port...')
        self.GetDataFromRadio()                  # read the serial port
        sleep(1)
        self.GetDataFromRadio()
        #print(config.received_datas)
        if len(config.received_datas) > 0:        # datas have been received
            print('Some datas to or from Radio were found. :-)\n')
            return True
        else:
            print ('Nothing heard, trying to switch it ON\n') # nothing received
            self.SendDataToRadio('PS1;')                # try to switch RADIO ON
            sleep(1)                                   # wait until radio wakes up
            self.SendDataToRadio('IF;')
            self.GetDataFromRadio()                              # read COM port
            sleep(1)
            self.GetDataFromRadio()

            if len(config.received_datas) > 0:
                print('Radio answering. :-) \n')
                return True
            else:
                print('No answer. :-(\nCheck wirings, settings.\n### BEWARE ### Some virtual port drivers need the real main port to be active for the virtual ports to work !\n') # if everything failed, problem !
                return False
                #input('Stopping. CTRL-C to stop')

########################################
# change radio mode
########################################
def ChangeMode(mode):
    #global RadioMode
    if mode == 'CW':
        strCat = 'MD3;'     # MODE = CW
        config.RadioMode = 'CW'
        # switch on backlight
        midi_out.write([ [[144,49,127],0], [[144,50,0],0], [[144,51,0],0] , [[144,52,0],0] ])
    elif mode == 'LSB':
        strCat = 'MD1;'
        config.RadioMode = 'SSB'
        # switch on backlight
        midi_out.write([ [[144,51,127],0] , [[144,49,0],0] , [[144,50,0],0] , [[144,52,0],0] ])
    elif mode == 'USB':
        strCat = 'MD2;'
        config.RadioMode = 'SSB'
        # switch on backlight
        midi_out.write([ [[144,51,0],0] , [[144,49,0],0] , [[144,50,127],0] , [[144,52,0],0] ])
    elif mode == 'FSK':
        strCat = 'MD6;'
        config.RadioMode = 'FSK'
        # switch on backlight
        midi_out.write([ [[144,52,127],0] , [[144,49,0],0] , [[144,50,0],0] , [[144,51,0],0] ])
    ts590.SendDataToRadio(strCat)

########################################
# put radio on VFO A
########################################
def ChangeVFO(vfo):
    if vfo == 'A':
        strCat='FR0;'
        # switch on backlight
        midi_out.write([ [[144,35,127],0] , [[144,34,0],0] , [[144,3,0],0] , [[144,4,0],0] ])
    elif vfo == 'B':
        strCat='FR1;'
        # switch on backlight
        midi_out.write([[[144,34,127],0] , [[144,35,0],0] , [[144,3,0],0] , [[144,4,0],0] ])
    ts590.SendDataToRadio(strCat)

########################################
# put RIT OFF
########################################
def PutRITOFF():
    ts590.SendDataToRadio('RT0;')           # RIT OFF
    config.RITisON = 0
    midi_out.write([[[144,83,0],0]])

#####################################
# init the Midi devices
#####################################
def InitMidiDevice(MidiDeviceIn):
    pygame.midi.init()

    # count the number of Midi devices connected
    MidiDeviceCount = pygame.midi.get_count()
    print ("Number of Midi devices found =",MidiDeviceCount)

    # display list of infos about all Midi devices found
    print("\nInfos about Midi devices :")
    for n in range(pygame.midi.get_count()):
        print (n,pygame.midi.get_device_info(n))

    """
    # display the default Midi device
    print("\nWindows default Midi input device =",pygame.midi.get_default_input_id())
    print("Windows default Midi output device =",pygame.midi.get_default_output_id())
    """

    # display Midi device selected by config file
    print ("\nConfig file selected Midi INPUT device =", config.MidiDeviceIn)
    print ("Config file selected Midi OUTPUT device =", config.MidiDeviceOut)

    # check if the selected input device is correct
    info = pygame.midi.get_device_info(config.MidiDeviceIn)     # get infos about input device, returns (interf, name, input, output, opened)
    #print (info)
    #print (info[0])
    try:
        if info == None:        # if out of range, pygame class returns None
            input("Device number out of range\nCTRLC-C and correct this")
            sys.exit(1)
        elif info[4] == 1:      # "opened" var in tuple returned, if 1 then device opened
            input ("Device already in use !\nCTRLC-C and correct this")
            sys.exit(1)
        elif info[2] != 1:      # "input" var in tuple returned, if 1 then device is an input
            input ("Device is not an input !\nCTRLC-C and correct this")
            sys.exit(1)
    except:
        pass

    # check if the selected output device is correct, same tests as above
    info = pygame.midi.get_device_info(config.MidiDeviceOut)
    #print (info)
    #print (info[0])
    try:
        if info == None:
            input("Device number out of range !\nCTRLC-C and correct this")
            sys.exit(1)
        elif info[4] == 1:
            input ("Device already in use !\nCTRLC-C and correct this")
            sys.exit(1)
        elif info[3] != 1:
            print("This device is not an output !\nCTRLC-C and correct this ")
            sys.exit(1)
    except:
        pass
    pygame.midi.init()          # init gain, just in case


###########################################
# switch ON all backlights on Midi console
###########################################
def ledsON():
    midi_out.write([ [[144,1,127],0], [[144,2,127],0], [[144,3,127],0] , [[144,4,127],0] , [[144,33,127],0], [[144,34,127],0], [[144,35,127],0] , [[144,49,127],0], [[144,50,127],0], [[144,51,127],0] , [[144,52,127],0] , [[144,81,127],0], [[144,82,127],0], [[144,83,127],0] , [[144,43,127],0] , [[144,45,127],0] , [[144,48,127],0] ])

###########################################
# switch OFF all backlights on Midi console
###########################################
def ledsOFF():
    midi_out.write([ [[144,1,0],0], [[144,2,0],0], [[144,3,0],0] , [[144,4,0],0] , [[144,33,0],0], [[144,34,0],0], [[144,35,0],0] , [[144,49,0],0], [[144,50,0],0], [[144,51,0],0] , [[144,52,0],0] , [[144,81,0],0], [[144,82,0],0], [[144,83,0],0] , [[144,43,0],0] , [[144,45,0],0] , [[144,48,0],0] ])

###########################################
# blink all backlights on Midi console
###########################################
def blinkLED(numTimes,period):
    for i in range(0,numTimes):## Run loop numTimes
        ledsON()
        sleep(period)
        ledsOFF()
        sleep(period)

########################################
# main loop read Midi, convert and send to radio
########################################
#http://stackoverflow.com/questions/15768066/reading-piano-notes-on-python/24821493#24821493
def readInput(input_device):
    while True:
        #ts590.GetDataFromRadio()           # if we want to listen to the datas coming from the radio,n ot needed for now
        if input_device.poll():
            event = input_device.read(1)[0]
            print (event)

            data = event[0]
            #print (data)
            #timestamp = event[1]

            device=data[0]
            status = data[1]
            control = data[2]
            value = data[3]

            # for debugging
            #print (device)
            #print(status)
            #print (control)
            #print (value)

            #detect rotation of jogs and pots
            if device == 176:
                if status == 49:
                    if control >64:
                        strCat = 'RD;'      # RIT DOWN
                        ts590.SendDataToRadio(strCat)
                    else:
                        strCat ='RU;'       # RIT UP
                        ts590.SendDataToRadio(strCat)
                elif status == 48:
                    if control < 64:
                        strCat = 'UP;'      # VFO UP
                        ts590.SendDataToRadio(strCat)
                    else :
                        strCat = 'DN;'      # VFO DOWN
                        ts590.SendDataToRadio(strCat)
                elif status == 54:                              # SLIDER
                    strCat = format ("AG%04d;"% ( control ))    # RX VOLUME
                    ts590.SendDataToRadio(strCat)
                elif status == 60 and config.RadioMode =='CW':         # CW bandwidth
                    print ("%04d"% (math.floor(100 + (1000 - 100) * control / 127 )))
                    strCat = format ("FW%04d;"% (math.floor(100 + (1000 - 100) * control / 127 )))
                    ts590.SendDataToRadio(strCat)
                elif status == 60 and config.RadioMode =='FSK':
                    print ("%04d"% (math.floor(250 + (1500 - 250) * control / 127 )))
                    strCat = format ("FW%04d;"% (math.floor(250 + (1500 - 250) * control / 127 )))
                    ts590.SendDataToRadio(strCat)
                elif status == 59:
                    print (math.floor(( control / 11)))         # SH command 00-11
                    strCat = format ("SL%02d;"% (math.floor( control / 11 )))
                    ts590.SendDataToRadio(strCat)
                elif status == 63:
                    print (math.floor(( control / 9.5 )))       # SL command 00-13
                    strCat = format ("SH%02d;"% (math.floor( control / 9 )))
                    ts590.SendDataToRadio(strCat)
                elif status == 64:                              # CW shift command IS
                    #GetModeFromRadio()
                    print ("%04d"% (math.floor(300 + (1000 - 300) * control / 127 )))
                    strCat = format ("IS %04d;"% (math.floor(300 + (1000 - 300) * control / 127 )))
                    ts590.SendDataToRadio(strCat)
                elif status == 61:                              # sets the power 005-100
                    #GetModeFromRadio()
                    print ("%03d"% (math.floor(5 + (100 - 5) * control / 127 )))
                    strCat = format ("PC%03d;"% (math.floor(5 + (100 - 5) * control / 127 )))
                    ts590.SendDataToRadio(strCat)

            # detects buttons
            if device == 144:
                if status == 1 and control == 127:      # TF-SET pressed
                    ts590.SendDataToRadio('TS1;')       # TF-SET ON
                    midi_out.write([[[144,1,127],0]])
                elif status == 1 and control == 0:      # TF-SET released
                    ts590.SendDataToRadio('TS0;')       # TF-SET OFF
                    midi_out.write([[[144,1,0],0]])
                elif status == 3 and control == 127:                       # RX VFO-A TX VFO-B
                    ts590.SendDataToRadio('FR0;FT1;')
                    midi_out.write([ [[144,3,127],0] , [[144,4,0],0] , [[144,34,127],0] , [[144,35,127],0] ])
                elif status == 4 and control == 127:                       # RX VFO-B TX VFO-A
                    ts590.SendDataToRadio('FR1;FT0;')
                    midi_out.write([ [[144,4,127],0] ,[[144,3,0],0] , [[144,34,127],0] , [[144,35,127],0] ])
                elif status == 35 and control == 127:                      # VFO A
                    ChangeVFO('A')
                elif status == 34 and control == 127:                      # VFO B
                    ChangeVFO('B')
                elif status == 33:    # II> key pressed
                    if control == 127:
                        ts590.SendDataToRadio('VV;')       # A=B
                        midi_out.write([[[144,33,127],0]])
                    else:
                        midi_out.write([[[144,33,0],0]])
                elif status == 2:                           # CUE2 key
                    if control == 127:                      # key pressed
                        ts590.SendDataToRadio('CA1;')       # CW tune ON
                        midi_out.write([[[144,2,127],0]])   # REC backlight ON
                    else:                                   # key released
                        ts590.SendDataToRadio('CA0;')       # CW tune OFF
                        midi_out.write([[[144,2,0],0]])      # REC backlight OFF
                elif status == 43 and control == 127:       # if REC key pressed
                    if config.RadioIsON == 1:                      # if radio is already ON
                        ts590.SendDataToRadio('PS0;')       # send OFF to radio
                        ledsOFF()                           # switch OF Fall backlights
                        config.RadioIsON = 0                       # set flag OFF
                    elif config.RadioIsON == 0:                    # if radio is OFF
                        config.RadioIsON = 1
                        ts590.SendDataToRadio('PS1;')       # send radio ON
                        midi_out.write([[[144,43,127],0]])  # SWITCH ON BACKLIGHT LED
                        sleep(2)                             # time for the radio to wake up
                        # switch radio to default mode
                        ChangeMode(config.RadioDefaultMode)
                        sleep(0.5)
                        # put radio to default VFO
                        ChangeVFO(config.RadioDefaultVFO)
                        sleep(0.5)
                        # switch OFF RIT
                        PutRITOFF()


                elif status == 83 and control == 127:                          # SYNC B key
                    if config.RITisON == 0:
                        ts590.SendDataToRadio('RT1;')       # RIT ON
                        midi_out.write([[[144,83,127],0]])
                        config.RITisON = 1
                    elif config.RITisON == 1:
                        PutRITOFF()


                elif status == 82 and control == 127:
                    if config.XITisON == 0:
                        ts590.SendDataToRadio('XT1;')       # XIT ON
                        midi_out.write([[[144,82,127],0]])
                        config.XITisON = 1
                    elif config.XITisON == 1:
                        ts590.SendDataToRadio('XT0;')       # XIT ON
                        midi_out.write([[[144,82,0],0]])
                        config.XITisON = 0


                elif status == 81 and control == 127:
                    ts590.SendDataToRadio('RC;') # RIT CLEAR

                elif status == 49 and control == 127:
                    ChangeMode('CW')
                elif status == 50 and control == 127:
                    ChangeMode('USB')
                elif status == 51 and control == 127:      # MODE = USB
                    ChangeMode('LSB')
                elif status == 52 and control == 127:
                    ChangeMode('FSK')
                # for debugging uncomment 2 next lines
                #else:
                #    print("Nothing affected")


###########################################
# Let's start !
###########################################
if __name__ == '__main__':

    print ("\n%s - (c) Patrick EGLOFF aka TK5EP" %(Name))
    print ("Version %s, date : %s\n" % (Version, VersionDate))

    # check if ini file exists and read the settings
    inifile = 'midi2ts590.ini'
    if os.path.isfile(inifile):
        ReadIniFile()
    else:
        print('\nConfiguration file does not exist !\nCreating it in a few seconds, then edit it to your needs if something goes wrong.\n')
        sleep(5)
        CreateIniFile()

    # create serial port object
    ts590 = SerialCom()

    # open radio port
    if (ts590.open_comport()):
        print ('Radio model :',config.RadioModel,'on',ts590.serial.port)
        print ('Baudrate=',ts590.serial.baudrate,'Bits=',ts590.serial.bytesize,'Stop=',ts590.serial.stopbits,'Parity=',ts590.serial.parity)
        print ("Flow controls: XOn/XOff=",ts590.serial.xonxoff,"RTS/CTS=",ts590.serial.rtscts,"DSR/DTR=",ts590.serial.dsrdtr)
        print ("Lines: RTS=",ts590.serial.rts,"DTR=",ts590.serial.dtr,"CTS=",ts590.serial.cts,"DSR=",ts590.serial.dsr,"Timeout=",ts590.serial.timeout,"\n")

    else:
        print(config.RadioPort,"not available, busy or bad setting !")
        print("Below are available ports, set one in the configuration file")
        ts590.find_comports()       # show a list of found comports
        input('\nStopping. CTRL-C to stop')
        sys.exit()

        # check is radio is answering
    if (ts590.CheckRadio()):
        print ("Radio communication OK\n")
    else:
        ts590.close_comport()
        input('\nCTRL-C to EXIT')
        sys.exit(0)

    # init MIDI devices and set inut/output device
    InitMidiDevice(config.MidiDeviceIn)
    my_input = pygame.midi.Input(config.MidiDeviceIn) # open Midi devices
    midi_out = pygame.midi.Output(config.MidiDeviceOut)

    # blink all backlights as a test
    blinkLED(3,0.3)

    strCat='PS1;'                       # send radio ON
    ts590.SendDataToRadio(strCat)
    config.RadioIsON = 1                # flag for radio ON/OFF state
    midi_out.write([[[144,43,127],0]])  # SWITCH ON BACKLIGHT LED
    sleep(2)                             # time for the radio to wake up

    ChangeMode(config.RadioDefaultMode) # switch radio to default mode
    sleep(0.5)
    ChangeVFO(config.RadioDefaultVFO)   # put radio to default VFO
    sleep(0.5)
    PutRITOFF() # switch OFF RIT


    # if something has been setup in the commands section of the config file, send the TS590s commands to the radio
    if config.Radiocmd1 != '':
        print("Sending cmd " + config.Radiocmd1)
        ts590.SendDataToRadio(config.Radiocmd1)
        sleep(0.5)
    if config.Radiocmd2 != '':
        print("Sending cmd " + config.Radiocmd2)
        ts590.SendDataToRadio(config.Radiocmd2)
        sleep(0.5)
    if config.Radiocmd3 != '':
        print("Sending cmd " + config.Radiocmd3)
        ts590.SendDataToRadio(config.Radiocmd3)


    print("Ready!\n")

    readInput(my_input) # start reading Midi input in a loop
