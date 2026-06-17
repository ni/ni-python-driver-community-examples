#!/usr/bin/env python3
"""NI-DCPower Pulse Voltage.

This example demonstrates how to use the DCPower Pulse API to generate a single
voltage pulse using NI-DCPower.

The example uses the default resource name, channel, current level,
and voltage limit. Modify these values as needed for your measurement setup.

HOW TO RUN:
-----------
i.   From terminal (with default values):
        python nidcpower_pulse_voltage.py

ii.  From terminal (with custom values):
        python nidcpower_pulse_voltage.py -n "PXI1Slot1" -pvl 2.0 -pnt 2e-3

iii. To simulate without hardware:
        PowerShell:  python nidcpower_pulse_voltage.py -op 'Simulate=1, DriverSetup=Model:4139; BoardType:PXIe'
        cmd.exe:     python nidcpower_pulse_voltage.py -op "Simulate=1, DriverSetup=Model:4139; BoardType:PXIe"

"""

# Module imports
import argparse    # For parsing command-line arguments
import nidcpower   # NI-DCPower instrument driver
import sys         # For accessing command-line arguments via sys.argv


def example(resource_name, options, pulse_voltage_level, pulse_voltage_level_range, pulse_bias_voltage_level,
            pulse_current_limit, pulse_current_limit_range, pulse_bias_current_limit,
            pulse_off_time, pulse_on_time, pulse_bias_delay, aperture_time, source_delay):
    """
    Core measurement logic — sources a single voltage pulse and returns the measurement.

    Args:
        resource_name (str)              : NI-MAX resource name, eg: "PXI1Slot1"
        options (str or dict)            : Driver options, eg: "" or simulate dict
        pulse_voltage_level (float)      : Voltage level during the pulse (V), eg: 1.0 → 1 V
        pulse_voltage_level_range (float): Voltage level range during the pulse (V)
        pulse_bias_voltage_level (float) : Bias voltage between pulses (V)
        pulse_current_limit (float)      : Current limit during pulse (A), eg: 10e-3 → 10 mA
        pulse_current_limit_range (float): Current limit range during pulse (A)
        pulse_bias_current_limit (float) : Current limit between pulses (A)
        pulse_off_time (float)           : Duration of the pulse off period (s)
        pulse_on_time (float)            : Duration of the pulse on period (s)
        pulse_bias_delay (float)         : Delay before applying bias between pulses (s)
        aperture_time (float)            : Measurement aperture time (s)
        source_delay (float)             : Delay before sourcing the pulse (s)

    Returns:
        Measurement result — [voltage, current, in_compliance]
    """
    # 'with' block ensures session.abort() + session.close() are called automatically on exit.
    with nidcpower.Session(resource_name=resource_name, options=options) as session:

        # Configure source mode and output function.
        session.source_mode = nidcpower.SourceMode.SINGLE_POINT
        session.output_function = nidcpower.OutputFunction.PULSE_VOLTAGE

        # Configure pulse voltage parameters — level, range, and bias voltage.
        session.pulse_voltage_level = pulse_voltage_level
        session.pulse_voltage_level_range = pulse_voltage_level_range
        session.pulse_bias_voltage_level = pulse_bias_voltage_level

        # Configure pulse current limits — limit, range, and bias limit.
        session.pulse_current_limit = pulse_current_limit
        session.pulse_current_limit_range = pulse_current_limit_range
        session.pulse_bias_current_limit = pulse_bias_current_limit

        # Configure pulse timing.
        session.pulse_off_time = pulse_off_time
        session.pulse_on_time = pulse_on_time
        session.pulse_bias_delay = pulse_bias_delay

        # Set aperture time via configure_aperture_time() and set source delay.
        session.configure_aperture_time(aperture_time=aperture_time, units=nidcpower.ApertureTimeUnits.SECONDS)
        session.source_delay = source_delay

        # Commit sends all settings to hardware before initiate.
        session.commit()

        # Initiate output via context manager, wait for source complete, then fetch.
        # session.reset() called inside the initiate block to clear pulse hardware state.
        # timeout=5 s for fetch — adjust for longer pulse cycles.
        with session.initiate():
            session.wait_for_event(event_id=nidcpower.Event.SOURCE_COMPLETE)
            measurements = session.fetch_multiple(count=1, timeout=5)
            session.reset()

        print(f'Measurements: \n- Voltage: {measurements[0][0]:f} V'
              f'\n- Current: {measurements[0][1]:f} A\n- In Compliance: {measurements[0][2]}')

    return measurements


def _main(argsv):
    # Parses command-line arguments and calls example() with the parsed values.
    parser = argparse.ArgumentParser(
        description='Pulse voltage: source a single voltage pulse and measure.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-n',   '--resource-name',               default='PXI1Slot1', help='Resource name of NI SMU')
    parser.add_argument('-pvl',  '--pulse-voltage-level',         default=1.0,    type=float, help='Pulse voltage level (V)')
    parser.add_argument('-pvlr', '--pulse-voltage-level-range',   default=6.0,    type=float, help='Pulse voltage level range (V)')
    parser.add_argument('-pvbl', '--pulse-bias-voltage-level',    default=0.0,    type=float, help='Bias voltage between pulses (V)')
    parser.add_argument('-pclt',  '--pulse-current-limit',         default=10e-3,  type=float, help='Current limit during pulse (A)')
    parser.add_argument('-pcltr', '--pulse-current-limit-range',   default=10e-3,  type=float, help='Current limit range during pulse (A)')
    parser.add_argument('-pbclt', '--pulse-bias-current-limit',    default=10e-3,  type=float, help='Current limit between pulses (A)')
    parser.add_argument('-pft',  '--pulse-off-time',              default=5e-3,   type=float, help='Pulse off time (s)')
    parser.add_argument('-pnt',  '--pulse-on-time',               default=1e-3,   type=float, help='Pulse on time (s)')
    parser.add_argument('-pbd',  '--pulse-bias-delay',            default=1e-6,   type=float, help='Pulse bias delay (s)')
    parser.add_argument('-at',  '--aperture-time',               default=0.1e-3, type=float, help='Aperture time (s)')
    parser.add_argument('-sd',   '--source-delay',                default=50e-6,  type=float, help='Source delay (s)')
    parser.add_argument('-op',  '--option-string',               default='',     type=str,   help='Driver option string, eg: "Simulate=1, DriverSetup=Model:4139; BoardType:PXIe"')
    args = parser.parse_args(argsv)
    example(
        resource_name=args.resource_name,
        options=args.option_string,
        pulse_voltage_level=args.pulse_voltage_level,
        pulse_voltage_level_range=args.pulse_voltage_level_range,
        pulse_bias_voltage_level=args.pulse_bias_voltage_level,
        pulse_current_limit=args.pulse_current_limit,
        pulse_current_limit_range=args.pulse_current_limit_range,
        pulse_bias_current_limit=args.pulse_bias_current_limit,
        pulse_off_time=args.pulse_off_time,
        pulse_on_time=args.pulse_on_time,
        pulse_bias_delay=args.pulse_bias_delay,
        aperture_time=args.aperture_time,
        source_delay=args.source_delay,
    )


def main():
    # Entry point — passes real CLI args to _main().
    _main(sys.argv[1:])


def test_example():
    # Simulated hardware test — runs example() with a virtual PXIe-4139 (no real HW needed).
    options = {'simulate': True, 'driver_setup': {'Model': '4139', 'BoardType': 'PXIe'}}
    example('PXI1Slot1', options, 1.0, 6.0, 0.0, 10e-3, 10e-3, 10e-3, 5e-3, 1e-3, 1e-6, 0.1e-3, 50e-6)


def test_main():
    # Simulated CLI test — runs _main() with simulate option string.
    cmd_line = ['--option-string', 'Simulate=1, DriverSetup=Model:4139; BoardType:PXIe']
    _main(cmd_line)


# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------
if __name__ == '__main__':
    main()
