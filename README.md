# midi2ts590
A Python 3 script to remote control a TS590 (but also other Kenwood transceivers) using a Hercules DJcontrol compact (other controllers may work too).

It needs the Pygame MIDI library as well as the PySerial to be installed.
BEWARE that the above libraries are compatible with your Python 3 version !

The TS590s has a set of remote command that allows to control it, either via the COM port or the USB port.
The goal of this script is to drive the TS590s via on of these ports, with the help of a DJcontrol compact MIDI controller.

The jogs, buttons, slider and potentiometers are used to control the frequency, modes, VFO, etc...
e.g the left PITCH jog is used to control the VFO frequency, while the center slider controls the AF volume.

The script transforms the MIDI commands to Kenwood remote commands.

Here is the reassignment view of the controller.
![DJcontrol_TS590](https://user-images.githubusercontent.com/1655173/212649541-284efeca-9e17-44fd-b9a6-b3fc8dd16bab.JPG)

At startup, the script reads a configuration file "midi2ts590.ini" where the needed settings are given.
If the file doesn't exist in the current folder, it is create with default parameters that have to be adapted for the indentend use.
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
    
Apart the COM port number and MIDI device numbers, these default parameters should work.
The script displays all MIDI devices found and both INPUT and OUTPUT devices number have to be given in the configuration file.

Errors in the configuration file, wrong settings or not found devices do stop the execution.

Have fun & let me know if you found any interest in this script.
