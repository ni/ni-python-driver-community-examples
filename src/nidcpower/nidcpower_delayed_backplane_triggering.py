#!/usr/bin/env python3
"""
NI-DCPower SMU Delayed Backplane Triggering

This example demonstrates how to configure two NI-DCPower SMUs such that:
1. SMU1 generates a Source Complete Event.
2. The Source Complete Event is delayed using source_delay.
3. SMU2 waits for this event as a digital edge trigger.
4. The trigger is automatically routed through the PXI backplane.
5. Both SMUs perform sourcing and measurement operations.

HOW TO RUN:
-----------
i.   From terminal (with default values):
        python nidcpower_delayed_backplane_triggering.py

ii.  From terminal (with custom values):
        python nidcpower_delayed_backplane_triggering.py -n1 "NISMU1" -n2 "NISMU2" -sd 50e-6 -vl1 1.0 -vl2 1.0 -of "DC_VOLTAGE" -t 6

iii. To simulate without hardware:
        python nidcpower_delayed_backplane_triggering.py -op "Simulate=1, DriverSetup=Model:4139; BoardType:PXIe"

"""

import argparse    # For parsing command-line arguments
import sys         # For accessing command-line arguments via sys.argv
import nidcpower   # NI-DCPower instrument driver

def example(smu1_resource_name, smu2_resource_name, source_delay, voltage_smu1, voltage_smu2, output_function, event_timeout, options):
    # Create sessions for both SMUs using context managers to ensure proper resource management.
    """
    Args:
    smu1_resource_name (str): Resource name of the triggering SMU.
    smu2_resource_name (str): Resource name of the triggered SMU.
    source_delay (float): Delay in seconds before SMU1 generates the Source Complete Event.
    voltage_smu1 (float): Voltage level for SMU1.
    voltage_smu2 (float): Voltage level for SMU2.
    output_function (str): Output function (DC_VOLTAGE or DC_CURRENT).
    event_timeout (float): Timeout in seconds for waiting for trigger event.
    options (str): Driver option string. Can be used to enable simulation.
    """
    with nidcpower.Session(resource_name=smu1_resource_name, options=options) as smu1, nidcpower.Session(resource_name=smu2_resource_name, options=options) as smu2: 
        
        #Configure SMU1 to generate a Source Complete Event after a delay, and configure SMU2 to wait for that event as a trigger.
        smu1.source_mode = nidcpower.SourceMode.SINGLE_POINT #setting source mode to single point for SMU1
        smu1.output_function = getattr(nidcpower.OutputFunction, output_function) #setting output function for SMU1
        smu1.voltage_level = voltage_smu1

        smu1.measure_when = (nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE) #setting measure when to automatically after source complete for SMU1
        smu1.source_trigger_type = nidcpower.TriggerType.NONE #setting source trigger type to none for SMU1 since it is the triggering SMU

        #Delay Source Complete Event generation
        smu1.source_delay = source_delay


        #Configure SMU2 to wait for SMU1's Source Complete Event as a trigger.
        smu2.source_mode = nidcpower.SourceMode.SINGLE_POINT #setting source mode to single point for SMU2
        smu2.output_function = getattr(nidcpower.OutputFunction, output_function) #setting output function for SMU2
        smu2.voltage_level = voltage_smu2

        smu2.measure_when = (nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE) #setting measure when to automatically after source complete for SMU2
        smu2.source_trigger_type = (nidcpower.TriggerType.DIGITAL_EDGE) #setting source trigger type to digital edge for SMU2

        # Use SMU1 Source Complete Event as trigger source
        smu2.digital_edge_source_trigger_input_terminal = (f"/{smu1.io_resource_descriptor}/Engine0/SourceCompleteEvent") #setting digital edge source trigger input terminal to SMU1's Source Complete Event for SMU2

        # Commit
        smu1.commit() #Commit SMU1 configuration to ensure it is ready to generate the Source Complete Event after the specified delay
        smu2.commit() #Commit SMU2 configuration to ensure it is ready to wait for the Source Complete Event from SMU1

        # Initiate
        smu2.initiate() # Initiate SMU2 first to ensure it is ready to receive the trigger
        smu1.initiate() # Initiate SMU1 to start the source operation, which will generate the Source Complete Event after the specified delay

        # Wait for triggered operation to complete
        smu2.wait_for_event(event_id=nidcpower.Event.SOURCE_COMPLETE, timeout=event_timeout)

        # Fetch Measurements
        smu1_measurement = smu1.fetch_multiple(count=1)[0]
        smu2_measurement = smu2.fetch_multiple(count=1)[0]

        print("SMU1 Measurement:")
        print(smu1_measurement)

        print("\nSMU2 Measurement:")
        print(smu2_measurement)

def _main(argsv):

    parser = argparse.ArgumentParser(description="NI-DCPower Delayed Backplane Trigger Example")

    parser.add_argument("-n1", "--smu1-resource-name", default="NISMU1", help="Triggering SMU resource name")
    parser.add_argument("-n2", "--smu2-resource-name", default="NISMU2", help="Triggered SMU resource name")
    parser.add_argument("-sd", "--source-delay", type=float, default=50e-6, help="Source Complete Event delay (seconds)")
    parser.add_argument("-v1", "--voltage-smu1", type=float, default=1.0, help="Voltage level for SMU1")
    parser.add_argument("-v2", "--voltage-smu2", type=float, default=1.0, help="Voltage level for SMU2")
    parser.add_argument("-of", "--output-function", type=str.upper, choices=["DC_VOLTAGE", "DC_CURRENT"], default="DC_VOLTAGE", help="Output function (DC_VOLTAGE or DC_CURRENT)")
    parser.add_argument("-t", "--event-timeout", type=float, default=6, help="Timeout in seconds for trigger event")
    parser.add_argument("-op", "--option-string", default="", help="Driver option string")

    args = parser.parse_args(argsv)

    example(
        smu1_resource_name= args.smu1_resource_name,
        smu2_resource_name= args.smu2_resource_name,
        source_delay= args.source_delay,
        voltage_smu1= args.voltage_smu1,
        voltage_smu2= args.voltage_smu2,
        output_function= args.output_function,
        event_timeout= args.event_timeout,
        options= args.option_string)


def main():
    #Entry point — passes real CLI args to _main().
    _main(sys.argv[1:])


def test_example():
    #Simulated hardware test —runs example() using NI-DCPower simulation.
    example(
        smu1_resource_name="NISMU1",
        smu2_resource_name="NISMU2",
        source_delay=50e-6,
        voltage_smu1=1.0,
        voltage_smu2=1.0,
        output_function="DC_VOLTAGE",
        event_timeout=6,
        options="Simulate=1,DriverSetup=Model:4139;BoardType:PXIe")

def test_main():
    #Simulated CLI test —runs _main() with simulate option string.

    cmd_line = ["-op","Simulate=1,DriverSetup=Model:4139;BoardType:PXIe"]
    _main(cmd_line)

# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------

if __name__ == '__main__':
    main()