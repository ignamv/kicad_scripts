# kicad_scripts
Utility Kicad scripts

## place_footprints.py

When you first start pcbnew and read a netlist,
all components are piled up in one place.
This script takes the schematic and pcb files 
and moves the footprints to match their placement in the schematic. 
This is a nicer starting point to route your PCB.

![Input schematic](/example_project/schematic.png?raw=true "Input schematic")
![Output pcb](/example_project/pcb.png?raw=true "Output PCB")
