#!/usr/bin/env python3
"""Leakage Test Example for NI Digital Pattern Instrument

This script demonstrates how to measure leakage current on DUT pins using a PXIe-6570/1 Digital Pattern Driver.
It applies configurable voltage levels to DUT pins via PPMU and measures the resulting current at each voltage to verify the device meets leakage specifications.

HOW TO RUN:
-----------
i.   From terminal (with default values):
        python nidigital_leakage_test.py

ii.  From terminal (with custom values):
        python nidigital_leakage_test.py -n "PXIe6570" -tv "0,3" -cl "25e-6" -pv "3.3" -at "20e-6" -dcl "10e-6" -pcl "10e-3"
        for more custom options, see the documentation of the example

iii. To simulate without hardware:
        PowerShell:  python nidigital_leakage_test.py -op 'Simulate=1, DriverSetup=Model:6571; BoardType:PXIe'
        cmd.exe:     python nidigital_leakage_test.py -op "Simulate=1, DriverSetup=Model:6571; BoardType:PXIe"  
"""

import argparse    # For parsing command-line arguments
import nidigital   # NI-Digital instrument driver
import os          # For constructing file paths (e.g., for the pin map file)
import sys         # For accessing command-line arguments via sys.argv

""" 
resource_name (str): NI-Digital resource name.
options (str): Driver option string.
test_voltages (list): Test voltage levels to apply to DUT pins.
current_limit (float): Leakage current threshold in Amps.
power_voltage (float): Power supply voltage for Power pins in Volts.
aperture_time (float): Measurement aperture time in Seconds.
dut_current_limit (float): Current limit range for DUT pins in Amps.
power_current_limit (float): Current limit range for Power pins in Amps.
Returns: list: Current measurements collected at each test voltage.
"""

def example(resource_name, options, test_voltages, current_limit, power_voltage,
            aperture_time, dut_current_limit, power_current_limit):
    currents = []
    pass_fail = []

    with nidigital.Session(resource_name=resource_name, reset_device=False, options=options) as session:

        # Store directory path
        dir_path = os.path.join(os.path.dirname(__file__))

        pin_map_filepath = os.path.join(dir_path, "PinMap.pinmap")
        session.load_pin_map(file_path=pin_map_filepath)

        # Set all pins to PPMU mode with specified aperture time
        session.channels["All_Pins"].selected_function = (nidigital.SelectedFunction.PPMU)
        session.channels["All_Pins"].ppmu_aperture_time_units = (nidigital.PPMUApertureTimeUnits.SECONDS)
        session.channels["All_Pins"].ppmu_aperture_time = aperture_time

        # Configure Power pins for supplying power to DUT and measuring current 
        session.channels["Power"].ppmu_output_function = (nidigital.PPMUOutputFunction.VOLTAGE)
        session.channels["Power"].ppmu_current_limit_range = power_current_limit
        session.channels["Power"].ppmu_voltage_level = power_voltage
        session.channels["Power"].ppmu_source()

        # Configure DUT pins for voltage forcing and current measurement with specified current limit range
        session.channels["DUTPins"].ppmu_current_limit_range = dut_current_limit
        session.channels["DUTPins"].ppmu_output_function = (nidigital.PPMUOutputFunction.VOLTAGE)
       
        pin_info = ( session.channels["DUTPins"].get_pin_results_pin_information()) 

         
        for i in range(len(test_voltages)): # Iterate through each test voltage level
            # Set the DUT pins to the current test voltage
            session.channels["DUTPins"].ppmu_voltage_level = (test_voltages[i]) 
            # Apply the voltage to the DUT pins
            session.channels["DUTPins"].ppmu_source() 
            # Measure the current drawn by the DUT pins and store the results
            currents.append(session.channels["DUTPins"].ppmu_measure(measurement_type=nidigital.PPMUMeasurementType.CURRENT))

            # Display measurement results 
            for j in range(len(pin_info)): #Iterate through each pin in the DUT to display measurement results

                result = (
                    "Pass"
                    if currents[i][j] <= current_limit
                    else "Fail"
                )
                # Append the result to the pass_fail list for later analysis
                pass_fail.append(result)
                ## Print the measurement results for this pin at the current voltage
                print(
                    f"{pin_info[j][0]} "
                    f"on Site {pin_info[j][1]} "
                    f"@ {test_voltages[i]}V: "
                    f"{currents[i][j]:3e}A "
                    f"--> {result}"
                )

        session.channels[""].selected_function = (nidigital.SelectedFunction.DISCONNECT)

    return currents 


def _main(argsv):
    #Parses command-line arguments and calls example() with the parsed values.
    parser = argparse.ArgumentParser(description="NI-Digital Leakage Current Example")
    parser.add_argument("-n", "--resource-name", default="PXI1Slot2", help="NI-Digital resource name")
    parser.add_argument("-op", "--options", default="", help="Driver options string")
    parser.add_argument("-tv", "--test-voltages", default="0,3,5", help="Test voltages as comma-separated values (default: 0,3,5)")
    parser.add_argument("-cl", "--current-limit", type=float, default=25e-6, help="Leakage current limit in Amps (default: 25e-6)" )
    parser.add_argument("-pv", "--power-voltage", type=float, default=3.3, help="Power supply voltage in Volts (default: 3.3)")
    parser.add_argument("-at","--aperture-time", type=float, default=20e-6, help="Aperture time in Seconds (default: 20e-6)")
    parser.add_argument( "-dcl","--dut-current-limit", type=float, default=10e-6, help="DUT pins current limit range in Amps (default: 10e-6)")
    parser.add_argument("-pcl","--power-current-limit", type=float, default=10e-3, help="Power pins current limit range in Amps (default: 10e-3)" )
    args = parser.parse_args(argsv)

    # Parse test voltages from comma-separated string
    test_voltages = [float(v) for v in args.test_voltages.split(",")]

    # Parse test voltages from comma-separated string
    test_voltages = [float(v) for v in args.test_voltages.split(",")]

    example(
        resource_name=args.resource_name,
        options=args.options,
        test_voltages=test_voltages,
        current_limit=args.current_limit,
        power_voltage=args.power_voltage,
        aperture_time=args.aperture_time,
        dut_current_limit=args.dut_current_limit,
        power_current_limit=args.power_current_limit
    )


def main():
    """Entry point — passes real CLI args to _main()."""
    _main(sys.argv[1:])


def test_example():
    # Simulated test — runs example() with hardcoded parameters.
    resource_name = "PXIe6570"
    options = "Simulate=1, DriverSetup=Model:6570; BoardType:PXIe"
    test_voltages=[0, 3, 5],
    current_limit= 25e-6,
    power_voltage=3.3,
    aperture_time=20e-6,
    dut_current_limit=10e-6,
    power_current_limit=10e-3
      
    example(resource_name=resource_name, options=options,test_voltages=test_voltages,
        current_limit= current_limit,
        power_voltage=power_voltage,
        aperture_time=aperture_time,
        dut_current_limit=dut_current_limit,
        power_current_limit=power_current_limit)

def test_main():
    #Simulated CLI test — runs _main() with simulate option string.
    cmd_line = ['--option-string', 'Simulate=1, DriverSetup=Model:6571; BoardType:PXIe']
    _main(cmd_line)

# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------

if __name__ == "__main__":
    main()