# midi2ts590
midi2ts590 is for **MIDI to TS590**<br />
It is a program written in Python to remote control a Kenwood TS590s radioamateur transceiver (probably other Kenwood transceivers as well) using a Hercules DJcontrol compact (other controllers may work too).

In 2017, I installed a remote station on a hilltop and I was in need of a convenient way to control my TS590s radio from home. So I wrote this simple program to do that with the help of a DJ controller.<br />
I chosed Python as programming language for the ease of use, and this is my first script written in Python.

Requirements
----
The program needs the **Pygame MIDI** as well as the **PySerial** libraries to be installed.

:warning: BEWARE that the above libraries are compatible with your Python 3 version !<br />
As of the date of writing (jan. 2023) the latest Pygame library is only compatible with the Windows packaged Python version 3.10.9

For what is it good for ?
----
The TS590s has a set of remote commands that allows to control it, either via the COM port or the USB port.<br />
The goal of this script is to remote control the TS590s via one of these ports with the help of a DJcontrol compact MIDI controller. This DJ controller has 2 big jogs, a set of pushbuttons, a slider potentiometer and 6 rotary potentioneter.

All these controls are used to change the frequency, modes, VFO, etc...<br />
e.g the left PITCH jog is used to control the VFO frequency, the right jog changes the RIT offset, while the center slider controls the AF volume, etc..

So, the script transforms the MIDI commands to Kenwood remote commands and sends them to the radio via the COM port.

Here is the reassignment view of the controller controls.
![DJcontrol_TS590](https://user-images.githubusercontent.com/1655173/212649541-284efeca-9e17-44fd-b9a6-b3fc8dd16bab.JPG)

 Usage
 ----
 There is NO need to load the driver for the used controller, it works as a standalone.<br />
 At startup, the script reads a configuration file "midi2ts590.ini" where the needed settings are given.  
:warning:If the file doesn't exist in the current folder, it is created with default parameters that have to be adapted for the indentend use !

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
    
Apart the COM port and MIDI device numbers, these default parameters should work.<br />
If a wrong COM port has been given, a list of found ports is displayed as a guide for correction.<br />
The script displays all MIDI devices found and both INPUT & OUTPUT device numbers have to be set in the configuration file.<br/>
Errors in the configuration file, wrong settings or not found devices do stop the execution.

For the initial tests, the TS590s can be connected directly to a COM port on the computer that also has the DJ controller attached. But this is really not very usefull...:smile:<br />
I use a pair of serial <-> Ethernet converters, one being on the local side and the other on the remote site. An Internet link between both sites makes this transparent.

As I also use a logging or contest software that must also take control over the radio, I use a virtual comport driver to share 2 (or more) virtual ports that are redirecting all commands to the real COM port hooked on the interface.<br />
I use **com0com virtual port driver** to do that.

FAQ
----


References & links
----
[My homepage](https://egloff.eu)<br />
[Hercules support page with all infos about the DJcontrol compact](https://support.hercules.com/en/product/djcontrolcompact-en/)<br />
[Kenwood remote control reference guide](https://www.kenwood.com/i/products/info/amateur/pdf/ts590_g_pc_command_en_rev3.pdf)

Have fun & let me know if you found any interest in this script.
Any comment & improvement is welcome.
