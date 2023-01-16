# midi2ts590
A Python 3 script to remote control a TS590 (but also other Kenwood transceivers) using a Hercules DJcontrol compact (other controllers may work too).

### Requirements ###
It needs the Pygame MIDI library as well as the PySerial to be installed.

:warning: BEWARE that the above libraries are compatible with your Python 3 version !<br />As of the date of writing (jan.2023) the last compatible Windows packaged Python version is 3.10.9

### For what is it good for ? ###
The TS590s has a set of remote command that allows to control it, either via the COM port or the USB port.<br />
The goal of this script is to drive the TS590s via on of these ports, with the help of a DJcontrol compact MIDI controller.

The jogs, buttons, slider and potentiometers are used to control the frequency, modes, VFO, etc...
e.g the left PITCH jog is used to control the VFO frequency, while the center slider controls the AF volume.

So, the script transforms the MIDI commands to Kenwood remote commands and sends them to the radio via the COM port.

Here is the reassignment view of the controller.
![DJcontrol_TS590](https://user-images.githubusercontent.com/1655173/212649541-284efeca-9e17-44fd-b9a6-b3fc8dd16bab.JPG)

### Usage ###
At startup, the script reads a configuration file "midi2ts590.ini" where the needed settings are given.  
:warning:If the file doesn't exist in the current folder, it is create with default parameters that have to be adapted for the indentend use !

Here the default values :

    [Default]
    # midi2ts590 config file
    # defaults values created by program
    mode = USB
    vfo = A

    [Midi]
    devicein = 1
    deviceout = 3

    [Radio]
    model = TS590s
    comport = COM33
    speed = 57600
    bits = 8
    stop = 1
    parity = N
    xonxoff = 0
    rtscts = 0
    dsrdtr = 0

    [Commands]
    # put one or more kenwood commands (see manual) on each following line
    # e.g cmd1 = vv;vx0;         set vfo a=b and vox off
    # e.g cmd2 = rt0;            will put rit off
    # these commands will be sent at startup
    cmd1 = 
    cmd2 = 
    cmd3 =
    
Apart the COM port number and MIDI device numbers, these default parameters should work.<br />
The script displays all MIDI devices found and both INPUT and OUTPUT devices number have to be given in the configuration file.

Errors in the configuration file, wrong settings or not found devices do stop the execution.
### References & links ###
[My homepage](https://egloff.eu)<br />
[Kenwood remote control reference guide](https://www.kenwood.com/i/products/info/amateur/pdf/ts590_g_pc_command_en_rev3.pdf)

Have fun & let me know if you found any interest in this script.
