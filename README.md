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

I have tested this script only on a **Windows 10** machine.

For what is it good for ?
----
The TS590s has a set of remote commands that allows to control it, either via the COM port or the USB port.<br />
The goal of this script is to remote control the TS590s via one of these ports with the help of a DJcontrol compact MIDI controller. This DJ controller has 2 big jogs, a set of pushbuttons, a slider potentiometer and 6 rotary potentioneter.

All these controls are used to change the frequency, modes, VFO, etc...<br />
e.g the left PITCH jog is used to control the VFO frequency, the right jog changes the RIT offset, while the center slider controls the AF volume, etc..

So, the script transforms the MIDI commands to Kenwood remote commands and sends them to the radio via the COM port.

Here is the reassignment view of the controller controls.<br />
![djcontrol_v023](https://user-images.githubusercontent.com/1655173/213935193-bb5455d5-ebbd-464a-a17c-0e65fb5cda53.jpg)


 Usage
 ----
        
    midi2ts590.py [-h] [-m] [-c] [-v]

    options:
      -h, --help      show this help message and exit
      -m, --midi      show available MIDI dervices
      -c, --comports  show COM ports
      -v, --verbose   increase output verbosity
  
 There is NO need to load the Hercules driver for the used controller, it works as a standalone.<br />
 At startup, the script reads a configuration file "midi2ts590.ini" where the needed settings are given.  
:warning:If the file doesn't exist in the current folder, it is created with default parameters that have to be adapted for the indentend use !

Here the default values :

     [Default]
     # midi2ts590 config file
     # defaults values created by program
     # see manual for help in setting
     mode = USB
     vfo = A
     tuningstep = 5
     radiosniff = 1

     [Midi]
     devicein = 1
     deviceout = 3

     [Radio]
     model = TS590s
     comport = COM8
     baudrate = 57600
     bytesize = 8
     stopbits = 1
     parity = N
     xonxoff = 0
     rtscts = 0
     dsrdtr = 0
     polltime = 1000
     rxtimeout = 100
     txtimeout = 100

     [Commands]
     # put one or more kenwood commands (see manual) on each following line
     # e.g cmd1 = vv;vx0;         set vfo a=b and vox off
     # e.g cmd2 = rt0;            will put rit off
     # these commands will be sent at startup
     cmd1 = VV
     cmd2 = 
     cmd3 = 

Apart the COM port and MIDI device numbers, these default parameters should work.<br />
If a wrong COM port has been given, a list of found ports is displayed as a guide for correction.<br />
The script displays all MIDI devices found and both INPUT & OUTPUT device numbers have to be set in the configuration file.<br/>
Errors in the configuration file, wrong settings or not found devices do stop the execution.

Some options need a bit more explanations:

    [Midi]
     devicein = 1
     deviceout = 3
     
These are MIDI device numbers of the DJcontroller. If you don't know what devices you have hooked on your computer, you can start the software with the -m or --midi option to show the devices found.<br />
List of all available MIDI devices, like this :
    
    nr: 0  Interface: MMSystem   Name: Microsoft MIDI Mapper            output   Opened:0
    nr: 1  Interface: MMSystem   Name: DJControl Compact                input    Opened:0
    nr: 2  Interface: MMSystem   Name: Microsoft GS Wavetable Synth     output   Opened:0
    nr: 3  Interface: MMSystem   Name: DJControl Compact                output   Opened:0

Set the right devices in the configuration file.

     tuningstep = 5
 
The VFO command is made via the left JOG button. Each increment in turning this button sends a increment command to the VFO of the radio.<br />
This can be a bit annoying as there is some latency due to the communication time between the software and the radio. To reduce this, each step on the tuning button can send more than one step. 5 seems to be quite adapted, but this can be adapted to everyone's need.

     radiosniff = 0
     
The settings made via the DJ controller are transmitted to the radio, and they are normaly "in phase".<br />
e.g The operating mode and VFO should be reported with the corresponding lights under the buttons.<br />
But when a modification is made on the radio itself with the help of the radio keyboard OR via a logging software that is also hooked on the radio, there can be some differences. Radio and controller are "out of phase".
This is for what the above option is good for.

With **radiosniff = 1**, the software is polling the radio and sending an "IF" command, waits for an answer and sets the controller to be in phase. This option presumes that there is no other software used.<br />
With **radiosniff = 2**, the software is polling the radio but doesn't send any command, it only "listens" what is on the COM port and detects the IF answer from the radio to the other logging software and modifies the LEDs state.<br />
**Radiosniff = 0** there is no sniffing at all.<br />
The polling time is set by default at 1 second, but can be modified with the **polltime** option, in ms.

For the initial tests, the TS590s can be connected directly to a COM port on the computer that also has the DJ controller attached. This can avoid some headaches with virtual ports, splitters, etc...<br />
But this isn't very usefull, as the target purpose is remote. :smile:<br />
I use a pair of serial <-> Ethernet converters, one being on the local side and the other on the remote site. An Internet link between both sites makes this transparent.

As I also use a logging or contest software that must also take control over the radio, I use a virtual comport driver to share 2 (or more) virtual ports that are redirecting all commands to the real COM port hooked on the interface.<br />
I use the freewares **com0com virtual port driver** and **hub4com** to do that.<br/>
<img src="https://user-images.githubusercontent.com/1655173/212717575-9c066f17-d594-4227-800a-ad413bfa5130.jpg" width="800">
<br />[More about this on my home page.](https://www.egloff.eu/index.php?option=com_content&view=article&id=94&Itemid=969&lang=en)

FAQ
----
**Is the Windows driver for the DJcontrol needed ?**<br />
No, it works as a standalone.

**Are other transceivers or DJ controller usable ?**<br />
Yes probably. Kenwood shares a large set between all models.<br />
The MIDI commands are quite standard, and adapting the codes in the software is possible.

References & links
----
[My homepage](https://egloff.eu)<br />
[Hercules support page with all infos about the DJcontrol compact](https://support.hercules.com/en/product/djcontrolcompact-en/)<br />
[Kenwood remote control reference guide](https://www.kenwood.com/i/products/info/amateur/pdf/ts590_g_pc_command_en_rev3.pdf)

Have fun & let me know if you found any interest in this script.
Any comment & improvement is welcome.
