#!/usr/bin/env python3
"""NI-DCPower Simultaneous Operation.

This example demonstrates how to program different outputs on multiple channels
on a single device. When the program runs, both channels will update their 
outputs to the specified Voltage Levels and take a voltage and current measurement.

The example uses the default resource name, channel, voltage level, current limit,
and current limit range. Modify these values as needed for your measurement setup.

HOW TO RUN:
-----------
i.   From terminal (with default values):
        python nidcpower_simultaneous_operation.py

ii.  From terminal (with custom values):
        python nidcpower_simultaneous_operation.py -n "PXI1Slot1" -vl0 3.0 -vl1 5.0

iii. To simulate without hardware:
        python nidcpower_simultaneous_operation.py -op "Simulate=1, DriverSetup=Model:4147; BoardType:PXIe"

"""

# Module imports
import argparse    # For parsing command-line arguments
import sys         # For accessing command-line arguments via sys.argv

import nidcpower   # NI-DCPower instrument driver


def example(resource_name, options, voltage_level_ch0, voltage_level_ch1,
            current_limit_ch0, current_limit_ch1,
            current_limit_range_ch0, current_limit_range_ch1, timeout):
    """
    Core measurement logic — sources DC voltage on two channels simultaneously and returns both measurements.

    Args:
        resource_name (str)            : NI-MAX resource name, eg: "PXI1Slot1"
        options (str or dict)          : Driver options, eg: "" or simulate dict
        voltage_level_ch0 (float)      : Voltage level for channel 0 (V), eg: 2.0 → 2 V
        voltage_level_ch1 (float)      : Voltage level for channel 1 (V), eg: 4.0 → 4 V
        current_limit_ch0 (float)      : Current limit for channel 0 (A), eg: 10e-3 → 10 mA
        current_limit_ch1 (float)      : Current limit for channel 1 (A)
        current_limit_range_ch0 (float): Current limit range for channel 0 (A)
        current_limit_range_ch1 (float): Current limit range for channel 1 (A)
        timeout (float)                : Timeout for waiting on Source Complete Event (s)

    """
    # 'with' block ensures session.abort() + session.close() are called automatically on exit.
    with nidcpower.Session(resource_name=resource_name, options=options) as session:

        # Configure source mode — SINGLE_POINT applies to all channels on the device.
        session.source_mode = nidcpower.SourceMode.SINGLE_POINT

        # Configure channel 0: output function, voltage level, and current limit.
        # Range is set before level to avoid range mismatch errors.
        session.channels[0].output_function = nidcpower.OutputFunction.DC_VOLTAGE
        session.channels[0].current_limit_range = current_limit_range_ch0
        session.channels[0].current_limit = current_limit_ch0
        session.channels[0].voltage_level = voltage_level_ch0

        # Configure channel 1: output function, voltage level, and current limit.
        session.channels[1].output_function = nidcpower.OutputFunction.DC_VOLTAGE
        session.channels[1].current_limit_range = current_limit_range_ch1
        session.channels[1].current_limit = current_limit_ch1
        session.channels[1].voltage_level = voltage_level_ch1

        # Commit sends all settings to hardware before initiate.
        session.commit()

        # Initiate output on both channels simultaneously.
        # wait_for_event(SOURCE_COMPLETE) blocks until the hardware has sourced the output.
        # measure_multiple() returns a list of [voltage, current, in_compliance] per channel.
        with session.initiate():
            session.wait_for_event(event_id=nidcpower.Event.SOURCE_COMPLETE, timeout=timeout)
            measurements = session.measure_multiple()

        print(f'Measurements ch0: \n- Voltage: {measurements[0][0]:f} V'
              f'\n- Current: {measurements[0][1]:f} A'
              f'\n- In Compliance: {measurements[0][2]}')
        print(f'Measurements ch1: \n- Voltage: {measurements[1][0]:f} V'
              f'\n- Current: {measurements[1][1]:f} A'
              f'\n- In Compliance: {measurements[1][2]}')


def _main(argsv):
    """Parses command-line arguments and calls example() with the parsed values."""
    parser = argparse.ArgumentParser(
        description='Simultaneous operation: source DC voltage on two channels and measure.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-n',    '--resource-name',            default='PXI1Slot1', help='Resource name of NI SMU')
    parser.add_argument('-vl0',   '--voltage-level-ch0',       default=2.0,   type=float, help='Voltage level for channel 0 (V)')
    parser.add_argument('-vl1',   '--voltage-level-ch1',       default=4.0,   type=float, help='Voltage level for channel 1 (V)')
    parser.add_argument('-cl0',  '--current-limit-ch0',        default=10e-3, type=float, help='Current limit for channel 0 (A)')
    parser.add_argument('-cl1',  '--current-limit-ch1',        default=10e-3, type=float, help='Current limit for channel 1 (A)')
    parser.add_argument('-clr0', '--current-limit-range-ch0',  default=10e-3, type=float, help='Current limit range for channel 0 (A)')
    parser.add_argument('-clr1', '--current-limit-range-ch1',  default=10e-3, type=float, help='Current limit range for channel 1 (A)')
    parser.add_argument('-t',    '--timeout',                  default=5.0,   type=float, help='Timeout for Source Complete Event (s)')
    parser.add_argument('-op',   '--option-string',            default='',    type=str,   help='Driver option string, eg: "Simulate=1, DriverSetup=Model:4162; BoardType:PXIe"')
    args = parser.parse_args(argsv)
    example(
        resource_name=args.resource_name,
        options=args.option_string,
        voltage_level_ch0=args.voltage_level_ch0,
        voltage_level_ch1=args.voltage_level_ch1,
        current_limit_ch0=args.current_limit_ch0,
        current_limit_ch1=args.current_limit_ch1,
        current_limit_range_ch0=args.current_limit_range_ch0,
        current_limit_range_ch1=args.current_limit_range_ch1,
        timeout=args.timeout,
    )


def main():
    """Entry point — passes real CLI args to _main()."""
    _main(sys.argv[1:])


def test_example():
    """Simulated hardware test — runs example() with a virtual PXIe-4147 (no real HW needed)."""
    options = {'simulate': True, 'driver_setup': {'Model': '4147', 'BoardType': 'PXIe'}}
    example('PXI1Slot1', options, 2.0, 4.0, 10e-3, 10e-3, 10e-3, 10e-3, 5.0)


def test_main():
    """Simulated CLI test — runs _main() with simulate option string."""
    cmd_line = ['--option-string', 'Simulate=1, DriverSetup=Model:4147; BoardType:PXIe']
    _main(cmd_line)


# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------
if __name__ == '__main__':
    main()
