
"""  Continuity Test Example for NI Digital Pattern Instrument
This script configures pins to source current and measure voltage to determine if pins are open, shorted, or have good continuity. It tests both positive and
negative clamp diodes by sourcing current in both directions. 
The pin map file this script configures pins to source current and measure voltage to determine if pins are open, shorted, or have good continuity. 
The pin map file can be modified to test different pins as needed.

 HOW TO RUN:
-----------
i.   From terminal (with default values):
        python nidigital_continuity.py
ii.  From terminal (with custom values):
        python nidigital_continuity.py -n "PXI1Slot2" -s False -fc 100e-6 -vhl 0.8 -vll 0.0
        for more custom options, see the documentation of the example

iii. To simulate without hardware:
        PowerShell:  python nidigital_continuity.py -op 'Simulate=1, DriverSetup=Model:6571; BoardType:PXIe'
        cmd.exe:     python nidigital_continuity.py -op "Simulate=1, DriverSetup=Model:6571; BoardType:PXIe" 
        
"""

import argparse
import nidigital
import os
import sys

"""
resource_name: NI Digital Pattern Instrument resource identifier 
options: Configuration options for the session
force_current: Current level to source (default: 100 uA)
voltage_high_limit: Upper voltage threshold for pass criteria
voltage_low_limit: Lower voltage threshold for pass criteria 

"""

def example(resource_name,options,force_current=100e-6,voltage_high_limit=0.8, voltage_low_limit=0.0):          
    voltages = []     # List to store voltage measurements from each test iteration
    with nidigital.Session(resource_name=resource_name, reset_device=False, options=options) as session:

        # Store directory path
        dir = os.path.join(os.path.dirname(__file__))

        # Load pin map
        pin_map_filename = os.path.join(dir, 'PinMap.pinmap')
        session.load_pin_map(file_path=pin_map_filename)

        # Set all pins to PPMU mode
        session.channels["All_Pins"].selected_function = nidigital.SelectedFunction.PPMU
        session.channels["All_Pins"].ppmu_aperture_time_units = nidigital.PPMUApertureTimeUnits.SECONDS
        session.channels["All_Pins"].ppmu_aperture_time = 20e-6

        # Configure Power pins to 0 V
        session.channels["All_Pins"].ppmu_output_function = nidigital.PPMUOutputFunction.VOLTAGE
        session.channels["All_Pins"].ppmu_current_limit_range = 10e-3
        session.channels["All_Pins"].ppmu_voltage_level = 0
        session.channels["All_Pins"].ppmu_source()

        # Configure DUT pins
        session.channels["All_Pins"].ppmu_current_level_range = 128e-6
        session.channels["All_Pins"].ppmu_voltage_limit_low = -1.5
        session.channels["All_Pins"].ppmu_voltage_limit_high = 1.5
        session.channels["All_Pins"].ppmu_output_function = nidigital.PPMUOutputFunction.CURRENT
        session.channels["All_Pins"].ppmu_current_level = force_current

        pin_info = session.channels["All_Pins"].get_pin_results_pin_information()

        print("Starting Continuity test")

        # Test positive and negative clamp diodes
        for i in range(2):
            session.channels["All_Pins"].ppmu_source()
            voltages.append(session.channels["All_Pins"].ppmu_measure(measurement_type=nidigital.PPMUMeasurementType.VOLTAGE))

            for j in range(len(pin_info)):

                if abs(voltage_low_limit) <= abs(voltages[i][j]) <= abs(voltage_high_limit):
                    pass_fail = "Pass"
                else:
                    pass_fail = "Fail"

                print(
                    f'{pin_info[j][0]} on Site {pin_info[j][1]} '
                    f'@ {session.channels["All_Pins"].ppmu_current_level:.3e} A: '
                    f'{voltages[i][j]:.3f} V --> {pass_fail}'
                )

            # Reverse current for negative clamp diode
            session.channels["DUTPins"].ppmu_current_level *= -1

        # Disconnect all pins
        session.selected_function = nidigital.SelectedFunction.DISCONNECT

    print("Continuity test complete")


def _main(argsv):
    #Parses command-line arguments and calls example() with the parsed values.
    parser = argparse.ArgumentParser(description='Continuity test using NI Digital Pattern Instrument',formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-n', '--resource-name', default='PXI1Slot2', help='NI Digital Pattern Instrument resource name')
    parser.add_argument('-s', '--simulate', default='False', choices=['True', 'False'], help='Run using simulated hardware')
    parser.add_argument('-fc', '--force-current', default=100e-6, type=float, help='PPMU force current')
    parser.add_argument('-vhl', '--voltage-high-limit', default=0.8, type=float, help='PPMU voltage high limit')
    parser.add_argument('-vll', '--voltage-low-limit', default=0.0, type=float, help='PPMU voltage low limit')
    args = parser.parse_args(argsv)

    example(resource_name=args.resource_name,
        options='Simulate=1, DriverSetup=Model:6571' if args.simulate == 'True' else '',
        force_current=args.force_current,
        voltage_high_limit=args.voltage_high_limit,
        voltage_low_limit=args.voltage_low_limit)

def main():
    #Entry point — passes real CLI args to _main().
    _main(sys.argv[1:])


def test_example():
    #Simulated hardware test — runs example() with a virtual PXIe-6571 (no real HW needed).
    resource_name = "PXI1Slot2"
    options = { "simulate": True, "driver_setup": {   "Model": "6571" }}
    force_current=100e-6, 
    voltage_high_limit=0.8,
    voltage_low_limit=0.0

    example(resource_name=resource_name, options=options, force_current=force_current, voltage_high_limit=voltage_high_limit, voltage_low_limit=voltage_low_limit)

def test_main():
    #Simulated CLI test — runs _main() with simulate option string.
    cmd_line = ['--option-string', 'Simulate=1, DriverSetup=Model:6571; BoardType:PXIe']
    _main(cmd_line)

# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------

if __name__ == '__main__':
    main()

