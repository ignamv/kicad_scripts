# kicad_scripts
Utility Kicad scripts

## place_footprints.py

When you first start pcbnew and read a netlist,
all components are piled up in one place.
This script takes the schematic and pcb files 
and moves the footprints to match their placement in the schematic. 
This is a nicer starting point to route your PCB.

### Instructions

You need to have python 2 installed. First, finish the schematic:

![Input schematic](/example_project/schematic.png?raw=true "Input schematic")

Then export the netlist for pcbnew,
and run cvpcb to associate a footprint to each component.
Launch pcbnew and load the netlist and footprint association, then save.
These are standard steps when making PCBs with Kicad, 
you can check out 
[Contextual Electronics](https://contextualelectronics.com/course/kicad-tutorial/) 
for more detailed instructions.

My script takes the pcb file you just saved
and moves the footprints to match the schematic.
You need to [download the script](place_footprints.py?raw=true) 
to your project directory.
To run it, just drag the project file (.pro) or project folder into the script icon.
Your pcb file now has placed components.

Here's the output from the schematic above:

![Output pcb](/example_project/pcb.png?raw=true "Output PCB")

If you want to see detailed script output (for troubleshooting),
open a terminal (in Windows, use Start -> Run -> cmd.exe)
and go to your project directory

    $ cd %USERPROFILE%\My Documents\example_project
    $ python place_footprints.py .
    Found project ./example_project
    Found schematic: ././example_project.sch
    Found pcb: ././example_project.kicad_pcb
    13:06:04: Debug: Skipping general section token 'links' 
    13:06:04: Debug: Skipping general section token 'area' 
    13:06:04: Debug: Skipping general section token 'drawings' 
    13:06:04: Debug: Skipping general section token 'tracks' 
    13:06:04: Debug: Skipping general section token 'zones' 
    13:06:04: Debug: Skipping general section token 'symbol' 
    Moving module...R1 R2 Q1 R4 C2 R3 C1 P1 P3 P2 
    Backing up ././example_project.kicad_pcb to ././example_project.kicad_pcb.bak6
