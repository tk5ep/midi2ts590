# midi2ts590
A Python 3 script to remote a TS590 using a Hercules DJcontrol compact.

The TS590s has a set of remote command that allows to control it, either via the COM port or the USB port.
The goal of this script is to drive the TS590s via on of these ports, with the help of a DJcontrol compact MIDI controller.

The jogs, buttons, slider and potentiometers are used to control the frequency, modes, VFO, etc...
e.g the left PITCH jog is used to control the VFO frequency, while the center slider controls the AF volume.

The script transforms the MIDI commands to Kenwood remote commands.

Here is the reassignment view of the controller.
![DJcontrol_TS590](https://user-images.githubusercontent.com/1655173/212649541-284efeca-9e17-44fd-b9a6-b3fc8dd16bab.JPG)

