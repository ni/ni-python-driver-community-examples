#!/usr/bin/env python3

"""  Continuity Test Example for NI Digital Pattern Instrument

This script configures pins to source current and measure voltage to determine if pins are open, shorted, or have good continuity. It tests both positive and negative clamp diodes by sourcing current in both directions. 

The pin map file in this script configures pins to source current and measure voltage to determine if pins are open, shorted, or have good continuity. 
The pin map file can be modified to test different pins as needed.

HOW TO RUN:
-----------
i.   From terminal (with default values):
        python nidigital_continuity_test.py

ii.  From terminal (with custom values):
        python nidigital_continuity_test.py -n "PXI1Slot2" -s False -pcl 100e-6 -tvlh 0.8 -tvll 0.0 -pat 20e-6 -pclr 10e-3 -pclvr 128e-6 -pvll -1.5 -pvlh 1.5
        for more custom options, see the documentation of the example

iii. To simulate without hardware:
        PowerShell:  python nidigital_continuity_test.py -op 'Simulate=1, DriverSetup=Model:6571; BoardType:PXIe'
        cmd.exe:     python nidigital_continuity_test.py -op "Simulate=1, DriverSetup=Model:6571; BoardType:PXIe" 

"""
# Module imports
import argparse    # For parsing command-line arguments
import nidigital   # NI-Digital instrument driver
import os          # For constructing file paths (e.g., for the pin map file)
import sys         # For accessing command-line arguments via sys.argv

"""
resource_name: NI Digital Pattern Instrument resource identifier 
options: Configuration options for the session
ppmu_current_level: Current level to source 
test_voltage_limit_high: Upper voltage threshold for pass criteria
test_voltage_limit_low: Lower voltage threshold for pass criteria 
ppmu_aperture_time: Aperture time for the PPMU 
ppmu_current_limit_range: Current limit range for the PPMU 
ppmu_current_level_range: Current level range for the PPMU 
ppmu_voltage_limit_low: Lower voltage limit for the PPMU 
ppmu_voltage_limit_high: Upper voltage limit for the PPMU 

"""

def example(resource_name, options, ppmu_current_level, test_voltage_limit_high, test_voltage_limit_low, ppmu_aperture_time, ppmu_current_limit_range, ppmu_current_level_range, ppmu_voltage_limit_low, ppmu_voltage_limit_high):          
    voltages = []     # List to store voltage measurements from each test iteration
    with nidigital.Session(resource_name=resource_name, reset_device=False, options=options) as session:

        # Store directory path
        dir_path = os.path.join(os.path.dirname(__file__))

        # Load pin map
        pin_map_filename = os.path.join(dir_path, 'PinMap.pinmap')
        session.load_pin_map(file_path=pin_map_filename)

        # Set all pins to PPMU mode to source current and measure voltage
        session.channels["All_Pins"].selected_function = nidigital.SelectedFunction.PPMU
        session.channels["All_Pins"].ppmu_aperture_time_units = nidigital.PPMUApertureTimeUnits.SECONDS
        session.channels["All_Pins"].ppmu_aperture_time = ppmu_aperture_time

        # Configure Power pins to 0 V and source current within specified limits to test clamp diodes
        session.channels["All_Pins"].ppmu_output_function = nidigital.PPMUOutputFunction.VOLTAGE
        session.channels["All_Pins"].ppmu_current_limit_range = ppmu_current_limit_range
        session.channels["All_Pins"].ppmu_voltage_level = 0
        session.channels["All_Pins"].ppmu_source()

        # Configure DUT pins to source current and measure voltage
        session.channels["All_Pins"].ppmu_current_level_range = ppmu_current_level_range
        session.channels["All_Pins"].ppmu_voltage_limit_low = ppmu_voltage_limit_low
        session.channels["All_Pins"].ppmu_voltage_limit_high = ppmu_voltage_limit_high
        session.channels["All_Pins"].ppmu_output_function = nidigital.PPMUOutputFunction.CURRENT
        session.channels["All_Pins"].ppmu_current_level = ppmu_current_level

        pin_info = session.channels["All_Pins"].get_pin_results_pin_information()

        print("Starting Continuity test")

        # Test positive and negative clamp diodes by sourcing current in both directions and measuring voltage response to determine if pins are open, shorted, or have good continuity.
        for i in range(2): # Two iterations: first with positive current, then with negative current to test both directions of clamp diodes
            session.channels["All_Pins"].ppmu_source()
            voltages.append(session.channels["All_Pins"].ppmu_measure(measurement_type=nidigital.PPMUMeasurementType.VOLTAGE))

            for j in range(len(pin_info)): # Iterate through each pin's information to evaluate voltage measurements against test limits and determine pass/fail status for continuity test

                if abs(test_voltage_limit_low) <= abs(voltages[i][j]) <= abs(test_voltage_limit_high): # Check if measured voltage is within specified limits for continuity test
                    pass_fail = "Pass"
                else:
                    pass_fail = "Fail"

                print(
                    f'{pin_info[j][0]} on Site {pin_info[j][1]} '
                    f"Current: {session.channels['All_Pins'].ppmu_current_level:.3e}A, "
                    f"Voltage: {voltages[i][j]:.3f}V, Status: {pass_fail}"
                )

            # Reverse current for negative clamp diode
            session.channels["All_Pins"].ppmu_current_level *= -1 # Reverse the current level to test negative clamp diodes in the second iteration

        # Disconnect all pins
        session.selected_function = nidigital.SelectedFunction.DISCONNECT

    print("Continuity test complete")


def _main(argsv):
    #Parses command-line arguments and calls example() with the parsed values.
    parser = argparse.ArgumentParser(description='Continuity test using NI Digital Pattern Instrument',formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-n', '--resource-name', default='PXI1Slot2', help='NI Digital Pattern Instrument resource name')
    parser.add_argument('-s', '--simulate', default='False', choices=['True', 'False'], help='Run using simulated hardware')
    parser.add_argument('-pcl', '--ppmu-current-level', default=100e-6, type=float, help='PPMU current level')
    parser.add_argument('-tvlh', '--test-voltage-limit-high', default=0.8, type=float, help='Test voltage high limit')
    parser.add_argument('-tvll', '--test-voltage-limit-low', default=0.0, type=float, help='Test voltage low limit')
    parser.add_argument('-pat', '--ppmu-aperture-time', default=20e-6, type=float, help='PPMU aperture time in seconds')
    parser.add_argument('-pclr', '--ppmu-current-limit-range', default=10e-3, type=float, help='PPMU current limit range')
    parser.add_argument('-pclvr', '--ppmu-current-level-range', default=128e-6, type=float, help='PPMU current level range')
    parser.add_argument('-pvll', '--ppmu-voltage-limit-low', default=-1.5, type=float, help='PPMU voltage limit low')
    parser.add_argument('-pvlh', '--ppmu-voltage-limit-high', default=1.5, type=float, help='PPMU voltage limit high')
    parser.add_argument('-op',  '--option-string', default='', type=str, help='Driver option string, eg: "Simulate=1, DriverSetup=Model:6571; BoardType:PXIe"')
    args = parser.parse_args(argsv)

    example(resource_name=args.resource_name,
    options=args.option_string,
    ppmu_current_level=args.ppmu_current_level,
    test_voltage_limit_high=args.test_voltage_limit_high,
    test_voltage_limit_low=args.test_voltage_limit_low,
    ppmu_aperture_time=args.ppmu_aperture_time,
    ppmu_current_limit_range=args.ppmu_current_limit_range,
    ppmu_current_level_range=args.ppmu_current_level_range,
    ppmu_voltage_limit_low=args.ppmu_voltage_limit_low,
    ppmu_voltage_limit_high=args.ppmu_voltage_limit_high)

def main():
    #Entry point — passes real CLI args to _main().
    _main(sys.argv[1:])


def test_example():
    #Simulated hardware test — runs example() with a virtual PXIe-6571 (no real HW needed).
    resource_name = "PXI1Slot2"
    options = { "simulate": True, "driver_setup": {   "Model": "6571" }}
    ppmu_current_level=100e-6, 
    test_voltage_limit_high=0.8,
    test_voltage_limit_low=0.0,
    pmu_aperture_time=20e-6, 
    ppmu_current_limit_range=10e-3, 
    ppmu_current_level_range=128e-6, 
    ppmu_voltage_limit_low=-1.5, 
    ppmu_voltage_limit_high=1.5

    example(resource_name=resource_name, options=options, ppmu_current_level=ppmu_current_level, test_voltage_limit_high=test_voltage_limit_high, test_voltage_limit_low=test_voltage_limit_low, pmu_aperture_time=pmu_aperture_time, ppmu_current_limit_range=ppmu_current_limit_range, ppmu_current_level_range=ppmu_current_level_range, ppmu_voltage_limit_low=ppmu_voltage_limit_low, ppmu_voltage_limit_high=ppmu_voltage_limit_high)

def test_main():
    #Simulated CLI test — runs _main() with simulate option string.
    cmd_line = ['--option-string', 'Simulate=1, DriverSetup=Model:6571; BoardType:PXIe']
    _main(cmd_line)

# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------

if __name__ == '__main__':
    main()

