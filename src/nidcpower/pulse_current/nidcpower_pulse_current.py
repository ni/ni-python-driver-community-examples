
#!/usr/bin/python
"""NI-DCPower Pulse Current.

This example demonstrates how to use the DCPower Pulse API to generate a single
current pulse using NI-DCPower.

The example uses the default resource name, channel, current level,
and voltage limit. Modify these values as needed for your measurement setup.
 
HOW TO RUN:
-----------
i.   From terminal (with default values):
        python nidcpower_pulse_current.py

ii.  From terminal (with custom values):
        python nidcpower_pulse_current.py -n "PXI1Slot1" -il 200e-3 -pt 2e-3
        for more custom options, see the documentation of the example

iii. To simulate without hardware:
        PowerShell:  python nidcpower_pulse_current.py -op 'Simulate=1, DriverSetup=Model:4139; BoardType:PXIe'
        cmd.exe:     python nidcpower_pulse_current.py -op "Simulate=1, DriverSetup=Model:4139; BoardType:PXIe"

"""

# Module imports
import argparse    # For parsing command-line arguments
import nidcpower   # NI-DCPower instrument driver
import sys         # For accessing command-line arguments via sys.argv


def example(resource_name, options, pulse_current_level, pulse_current_level_range, pulse_bias_current_level,
            pulse_voltage_limit, pulse_voltage_limit_range, pulse_bias_voltage_limit,
            source_delay, pulse_on_time, pulse_off_time, pulse_bias_delay, aperture_time):
    """
    Core measurement logic — sources a single current pulse and returns the measurement.

    Args:
        resource_name (str)              : NI-MAX resource name, eg: "PXI1Slot1"
        options (str or dict)            : Driver options, eg: "" or simulate dict
        pulse_current_level (float)      : Pulse current level (A), eg: 100e-3 → 100 mA
        pulse_current_level_range (float): Pulse current level range (A)
        pulse_bias_current_level (float) : Bias current between pulses (A)
        pulse_voltage_limit (float)      : Voltage limit during pulse (V)
        pulse_voltage_limit_range (float): Voltage limit range during pulse (V)
        pulse_bias_voltage_limit (float) : Voltage limit between pulses (V)
        source_delay (float)             : Delay before sourcing the pulse (s)
        pulse_on_time (float)            : Duration of the pulse on period (s)
        pulse_off_time (float)           : Duration of the pulse off period (s)
        pulse_bias_delay (float)         : Delay before applying bias between pulses (s)
        aperture_time (float)            : Measurement aperture time (s)

    Returns:
        Measurement result — [voltage, current, in_compliance]
    """
    # 'with' block ensures session.abort() + session.close() are called automatically on exit.
    with nidcpower.Session(resource_name=resource_name, options=options) as session:

        # Configure source mode and output function.
        session.source_mode = nidcpower.SourceMode.SINGLE_POINT
        session.output_function = nidcpower.OutputFunction.PULSE_CURRENT

        # Configure pulse current parameters — level, range, and bias current.
        session.pulse_current_level = pulse_current_level
        session.pulse_current_level_range = pulse_current_level_range
        session.pulse_bias_current_level = pulse_bias_current_level

        # Configure pulse voltage limits — limit, range, and bias limit.
        session.pulse_voltage_limit = pulse_voltage_limit
        session.pulse_voltage_limit_range = pulse_voltage_limit_range
        session.pulse_bias_voltage_limit = pulse_bias_voltage_limit

        # Configure pulse timing.
        session.source_delay = source_delay
        session.pulse_on_time = pulse_on_time
        session.pulse_off_time = pulse_off_time
        session.pulse_bias_delay = pulse_bias_delay

        # Set aperture time via properties (units first, then value).
        session.aperture_time_units = nidcpower.ApertureTimeUnits.SECONDS
        session.aperture_time = aperture_time

        # Initiate output, wait for pulse to complete, then fetch the result.
        # session.initiate() used directly (not as context manager) — consistent with pulse current pattern.
        # session.reset() called after fetch to clear pulse hardware state before session closes.
        session.initiate()
        session.wait_for_event(event_id=nidcpower.Event.PULSE_COMPLETE)
        measurements = session.fetch_multiple(count=1)
        session.reset()

        print(f'Measurements: \n- Voltage: {measurements[0][0]:f} V'
              f'\n- Current: {measurements[0][1]:f} A\n- In Compliance: {measurements[0][2]}')

    return measurements


def _main(argsv):
    """Parses command-line arguments and calls example() with the parsed values."""
    parser = argparse.ArgumentParser(
        description='Pulse current: source a single current pulse and measure.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-n',   '--resource-name',              default='PXI1Slot1', help='Resource name of NI SMU')
    parser.add_argument('-il',  '--pulse-current-level',        default=100e-3,  type=float, help='Pulse current level (A)')
    parser.add_argument('-ilr', '--pulse-current-level-range',  default=100e-3,  type=float, help='Pulse current level range (A)')
    parser.add_argument('-ibl', '--pulse-bias-current-level',   default=0.0,     type=float, help='Bias current between pulses (A)')
    parser.add_argument('-vl',  '--pulse-voltage-limit',        default=1.0,     type=float, help='Voltage limit during pulse (V)')
    parser.add_argument('-vlr', '--pulse-voltage-limit-range',  default=1.0,     type=float, help='Voltage limit range during pulse (V)')
    parser.add_argument('-vbl', '--pulse-bias-voltage-limit',   default=1.0,     type=float, help='Voltage limit between pulses (V)')
    parser.add_argument('-d',   '--source-delay',               default=50e-6,   type=float, help='Source delay (s)')
    parser.add_argument('-pt',  '--pulse-on-time',              default=0.001,   type=float, help='Pulse on time (s)')
    parser.add_argument('-pf',  '--pulse-off-time',             default=0.005,   type=float, help='Pulse off time (s)')
    parser.add_argument('-pb',  '--pulse-bias-delay',           default=1e-6,    type=float, help='Pulse bias delay (s)')
    parser.add_argument('-at',  '--aperture-time',              default=0.0001,  type=float, help='Aperture time (s)')
    parser.add_argument('-op',  '--option-string',              default='',      type=str,   help='Driver option string, eg: "Simulate=1, DriverSetup=Model:4139; BoardType:PXIe"')
    args = parser.parse_args(argsv)
    example(
        resource_name=args.resource_name,
        options=args.option_string,
        pulse_current_level=args.pulse_current_level,
        pulse_current_level_range=args.pulse_current_level_range,
        pulse_bias_current_level=args.pulse_bias_current_level,
        pulse_voltage_limit=args.pulse_voltage_limit,
        pulse_voltage_limit_range=args.pulse_voltage_limit_range,
        pulse_bias_voltage_limit=args.pulse_bias_voltage_limit,
        source_delay=args.source_delay,
        pulse_on_time=args.pulse_on_time,
        pulse_off_time=args.pulse_off_time,
        pulse_bias_delay=args.pulse_bias_delay,
        aperture_time=args.aperture_time,
    )


def main():
    """Entry point — passes real CLI args to _main()."""
    _main(sys.argv[1:])


def test_example():
    """Simulated hardware test — runs example() with a virtual PXIe-4139 (no real HW needed)."""
    options = {'simulate': True, 'driver_setup': {'Model': '4139', 'BoardType': 'PXIe'}}
    example('PXI1Slot1', options, 100e-3, 100e-3, 0.0, 1.0, 1.0, 1.0, 50e-6, 0.001, 0.005, 1e-6, 0.0001)


def test_main():
    """Simulated CLI test — runs _main() with simulate option string."""
    cmd_line = ['--option-string', 'Simulate=1, DriverSetup=Model:4139; BoardType:PXIe']
    _main(cmd_line)


# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------
if __name__ == '__main__':
    main()
