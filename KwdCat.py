#-------------------------------------------------------------------------------
# Name:        KwdCat
# Purpose:     A class to handle a COM port and Kenwood remote protocol
#
# Author:      Patrick EGLOFF aka TK5EP
#
# Created:     15/01/2023
# Copyright:   (c) Patrick EGLOFF 2023
# Licence:     GNU General Public License
#-------------------------------------------------------------------------------

__Title = "Python Kenwood CAT library"
__Version = "0.2"
__VersionDate = "27/01/2023"


## flag to be a bit verbose
DEBUG = False

## Imports
import re
import sys
import serial
from serial import SerialException
from serial.tools.list_ports import comports
from time import sleep

class KwdCat(object):
    """
    class to handle Kenwood remote control protocol
    """
    def find_ports(self):
        # show a list of current COM ports
        sys.stderr.write('\nBEWARE, some virtual ports may not be shown !\n')
        ports = []
        for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
            sys.stderr.write('{:2}: {:20} {!r}\n'.format(n, port, desc))
            ports.append(port)

    def open_port(self,port='COM1',baudrate=57600,bytesize=8,stopbits=1,parity='N',xonxoff=0,rtscts=0,dsrdtr=0,dtr=1,rts=1,rxtimeout=0,txtimeout=0) -> bool:
        # opens a COM port. These are values by default.
        # If a different value is needed, they must be given when calling
        #
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.stopbits = stopbits
        self.parity = parity
        self.xonxoff = xonxoff
        self.rtscts = rtscts
        self.dsrdtr = dsrdtr
        self.dtr = dtr
        self.rts = rts
        self.rxtimeout = rxtimeout
        self.txtimeout = txtimeout

        # define the serial port for radio
        try:
            print("\nOpening COM port...")
            self.serial = serial.Serial(        # set the port parameters
            port = self.port,
            baudrate = self.baudrate,
            bytesize = self.bytesize,
            stopbits = self.stopbits,
            parity = self.parity,
            xonxoff = self.xonxoff,             # software flow control
            rtscts = self.rtscts,               # hardware (RTS/CTS) flow control
            dsrdtr = self.dsrdtr,               # hardware (DSR/DTR) flow control
            timeout = self.rxtimeout,
            write_timeout = self.txtimeout)

            # setting RTS & DTR lines
            self.serial.dtr = self.dtr          # put DTR line HIGH
            self.serial.rts = self.rts          # put RTS line HIGH

            self.serial.is_open                 # open COM port
            return True
        except SerialException as msg:                 # if COM port communication problem
            print("Exception in open_port",msg)
            return False

    def close_port(self) -> bool:
        #################################
        # Close the comport
        #################################
        try:
            self.serial.close()
        except AttributeError:
            print("open_port has not been called yet !")
            return False
        else:
            print("Closing the COM port...")
            return True

    def send(self,datastosend:str):
        try:
            self.serial.write(datastosend.encode())
        except SerialException as msg:
            print('Exception in send :',msg)
            self.close_comport()

    def read(self) -> str:
        ########################################
        # read datas from radio
        ########################################
        try:
            received_data = self.serial.read_until(';')    # read serial port until we get a ; separator
            data_left = self.serial.inWaiting()            # check for remaining bytes
            received_data += self.serial.read(data_left)   # add remaining datas to buffer
            received_datas = (received_data.decode())   # decode in ASCII
            if DEBUG:
                print (received_datas)
            return received_datas
        except SerialException as msg:
            print("Serial exception in KwdCat.read function:",msg)
            return None
        except:
            print("Exception in KwdCat.read function")
            return  None

    def query(self, request: str,length:int) -> str:
        ########################################
        # usage query (request,length) -> query('IF',37)
        # input : request:str is the Kenwood command to find
        #         length:int is the awaited length of answer e.g IF awaits 37 char until the leading ; separator
        #         if length = 0, no answer is awaited (see Kenwood reference guide)
        # output : answer :str the cleaned answer from radio
        # sends a command to radio and returns the corresponding answer from radio
        # e.g send IF
        # returns IF00014050380      040000041020000080
        ########################################
        #if self.serial.isOpen:
            self.serial.reset_input_buffer()                    # flush the input buffer so we don't collect answers to other commands coming from other software
            send_string = f"{request.strip()};"                 # remove whitespaces if any and append terminator ;
            try:
                self.serial.write(send_string.encode())         # send data to serial port
            except SerialException as msg:
                print("Serial exception in query send function",msg)
                pass

            if length != 0:             #if we expect an answer
                try:
                    sleep(0.1)      # time to answer
                    recvd_data = self.serial.read_until(';')    # read serial port until we get a ; separator
                    data_left = self.serial.inWaiting()            # check for remaining bytes
                    recvd_data += self.serial.read(data_left)   # add remaining datas to buffer
                    answer = (recvd_data.decode())   # decode in ASCII
                    if DEBUG:
                        print ("Answer =",answer,"len=",len(answer))
                except SerialException as msg:
                    print("Serial exception in query read function :",msg)
                    pass

                ## find a block starting with the requested command
                ## and extract the full answer
                start = answer.find(request)
                if start != -1 and length < len(answer):                                     # if request string is found
                    if DEBUG:
                        print("Start position =",start)
                    if  answer[start + length] == ';':
                        answer = answer[start:start + length]
                        if DEBUG:
                            print ("Valid answer received :",answer)
                        return answer
                else:
                    return

    def checkradio(self) -> bool:
        #################################################
        # Check if Radio answering
        # returns True if OK
        # if not, tries to switch it ON
        # if no answer after this, returns False
        #################################################
        answer = self.query('IF',37)
        if answer is not None and len(answer) != 0: # if there is something in the answer
            print("Radio is answering")
            return True
        else:
            print("Trying to switch the radio ON")
            self.query('PS1',0)                     # send commande to switch ON
            sleep(1)
            answer = self.query('IF',37)
            if answer is not None and len(answer) != 0:     # we received something
                print ("Radio is now ON")
                return True
            else:
                print('No answer. :-(\nCheck wirings, settings.\n### BEWARE ### Some virtual port drivers need the real main port to be active for the virtual ports to work !\n') # if everything failed, problem !
                return False


    def ReadCmdIF(self,cmd:str)->list:
        ########################################
        # extracts status infos about radio
        # input:str. A string with a cleaned Kenwood cmd like IF00014050380      040000041020000080
        # ouput:list. A list with IFfreq,IFRitFreq,IFRitOnOff,IFXitOnOff,IFRxTx,IFMode,IFVfo,IFSplit
        ########################################
        # check if the frame is correspondonding to the awaited format
        pattern = re.compile(r"IF[0-9]{11}.{6}[0-9]{17}0", re.IGNORECASE)   # pattern to match the fram format
        if cmd is not None and pattern.match(cmd):              # if there is a match
            IFfreq = cmd[2:12]    # Freq of main VFO
            IFfreq = (IFfreq[:5] + '.' + IFfreq[5:]).lstrip('0')     # transform in MHz, insert dot and remove leading 000
            IFRitFreq = cmd[19:23]      # RIT value P3 in frame
            IFRitOnOff = cmd[23]        # RIT On/Off P4
            IFXitOnOff = cmd[24]        # XIT On/Off P5
            IFRxTx = cmd[28]            # P8
            IFMode = cmd[29]            # P9
            IFVfo = cmd[30]             # P10
            IFSplit = cmd[32]           # P12 split in frame

            return [IFfreq,IFRitFreq,IFRitOnOff,IFXitOnOff,IFRxTx,IFMode,IFVfo,IFSplit]
        else:
            if DEBUG:
                print("IF frame wrong decoding")
            return None
            pass

    def ReadCmdFAFB(self,cmd:str)->str:
        ###########################################
        # extracts VFO frequency from FA/FB command
        # input:str must be 13 char like FA00014049680
        # output:str freq in MHz with 5 decimals 14.12345
        ###########################################
        #if cmd is not None and len(cmd) == 13:                  # simple check, must be 17 char long
        pattern = re.compile(r"F[AB][0-9]{11}", re.IGNORECASE)
        if cmd is not None and pattern.match(cmd):
            VFOfreq = cmd[2:12]
            VFOfreq = (VFOfreq[:5] + '.' + VFOfreq[5:]).lstrip('0')       # transform in MHz, insert dot and remove leading 000
            return(VFOfreq)
        else:
            if DEBUG:
                print("FA/B frame wrong decoding")
            return None


    def ReadCmdXI(self,cmd:str)->list:
        ###########################################
        # extracts infos from XI command like XI000140496802000
        # input:str must be 17 char.
        # output:list freq in MHz with 5 decimals 14.12345, op mode & data mode
        ###########################################
        pattern = re.compile(r"XI[0-9]{13}00", re.IGNORECASE)
        if cmd is not None and pattern.match(cmd):
        #if cmd is not None and len(cmd) == 17:                  # simple check, must be 17 char long
            XIfreq = cmd[2:12]
            XIfreq = (XIfreq[:5] + '.' + XIfreq[5:]).lstrip('0')       # transform in MHz, insert dot and remove leading 000
            XImode = cmd[13]
            XIdata = cmd[14]
            return[XIfreq,XImode,XIdata]
        else:
            if DEBUG:
                print("XI frame wrong decoding")
            return None

    def ReadCmdPC(self,cmd:str)->list:
        ###########################################
        # extracts infos from PC (output power) command
        # input:str must be 5 char.
        # output:str 000-100
        ###########################################
        #if cmd is not None and len(cmd) == 5:                  # simple check
        pattern = re.compile(r"XI[0-9]{3}", re.IGNORECASE)
        if pattern.match(cmd):
            PCpower = cmd[2:5]
            return PCpower
        else:
            if DEBUG:
                print("PC frame wrong decoding")
            return None

    def ConvertMode(self,modenr:int) -> str:
        ########################################
        # returns readable mode  CW/LSB/RTTY etc from mode number
        # input:int 1-9
        # output:str
        ########################################
        if 1 <= modenr <= 9:                     # simple check
            modes=('','LSB','USB','CW','FM','AM','FSK','CW-R','None','FSK-R')
            return (modes[modenr])
        else:
            return None

    def FreqUp(self,step:int):              # like UP/DWN on mike, step 0-99
        self.query('UP',0)
    def FreqDown(self,step:int):            # like UP/DWN on mike, step 0-99
        self.query('DN',0)

    def VFOfreq(self,vfo=0,up=0,step=1):    # change VFO A/B freq, direction, step
        self.vfo = vfo                      # 0 =VFO A
        self.dir = up                       # 0 = up
        self.step = step                    # 1 = 1 step
        cmd='UD'
        strCat = f'{cmd}{self.vfo}{self.dir}{self.step:02}'
        self.query(strCat,0)
    def RITUp(self):
        self.query('RU',0)
    def RITDown(self):
        self.query('RD',0)
    def RITOnOff(self,state:int):
        self.state = state
        if self.state == 0:
            self.query('RT0',0)
        if self.state == 1:
            self.query('RT1',0)
    def XITOnOff(self,state:int):
        self.state = state
        if self.state == 0:
            self.query('XT0',0)
        if self.state == 1:
            self.query('XT1',0)
    def RadioOnOff(self,state:int):
        self.state = state
        if self.state == 1:
            self.query('PS1',0)
        if self.state == 0:
            self.query('PS0',0)



if __name__ == "__main__":
  print ("%s - (c) Patrick EGLOFF aka TK5EP" %(__Title))
  print ("Version %s, date : %s" % (__Version, __VersionDate))
  print ("This is a library, to be called from other modules. It does nothing by itself.")