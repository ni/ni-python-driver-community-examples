#!/usr/bin/env python3

"""NI-DCPower Single Point Multi-Channel Synchronization.

This example demonstrates how to use triggers and events to synchronize
multiple channels in Single Point source mode.
One output channel will operate as the master, and the others will be slaves.

The example uses the default resource names, channels, and source parameters.
Modify these values as needed for your measurement setup.

HOW TO RUN:
-----------
i.   From terminal (with default values):
        python nidcpower_single_point_multi_channel_sync.py

ii.  From terminal (with custom values):
        python nidcpower_single_point_multi_channel_sync.py \
            -mrn "PXI1Slot1" -mc "0" \
            -srn "PXI1Slot2" "PXI1Slot3" -sc "0" "0"

iii. To simulate without hardware (same model for all):
        PowerShell:  python nidcpower_single_point_multi_channel_sync.py \
            -mop 'Simulate=1, DriverSetup=Model:4147; BoardType:PXIe' \
            -sop 'Simulate=1, DriverSetup=Model:4147; BoardType:PXIe'
        cmd.exe:     python nidcpower_single_point_multi_channel_sync.py \
            -mop "Simulate=1, DriverSetup=Model:4147; BoardType:PXIe" \
            -sop "Simulate=1, DriverSetup=Model:4147; BoardType:PXIe"

iv.  To simulate without hardware (different models):
        PowerShell:  python nidcpower_single_point_multi_channel_sync.py \
            -mop 'Simulate=1, DriverSetup=Model:4139; BoardType:PXIe' \
            -sop 'Simulate=1, DriverSetup=Model:4147; BoardType:PXIe'
        cmd.exe:     python nidcpower_single_point_multi_channel_sync.py \
            -mop "Simulate=1, DriverSetup=Model:4139; BoardType:PXIe" \
            -sop "Simulate=1, DriverSetup=Model:4147; BoardType:PXIe"

"""

# Module imports
import argparse  # For parsing command-line arguments
import sys       # For accessing command-line arguments via sys.argv

import nidcpower  # NI-DCPower instrument driver


def example(
    master_resource_name, master_channel, slave_resource_names, slave_channels,
    master_options, slave_options, master_voltage_level,
    master_current_limit_range, master_current_limit, master_source_delay, slave_voltage_levels,
    slave_current_limit_ranges, slave_current_limits, slave_source_delay):
    """
    Perform synchronized single point sourcing and measurement across
    multiple NI-DCPower SMUs (one master, multiple slaves).

    Args:
        master_resource_name (str):
            NI-DCPower device identifier for the master SMU (eg: "PXI1Slot1")

        master_channel (str):
            Channel number for the master SMU (eg: "0")

        slave_resource_names (list of str):
            NI-DCPower device identifiers for the slave SMUs
            eg: ["PXI1Slot2", "PXI1Slot3"]

        slave_channels (list of str):
            Channel numbers for each slave SMU
            eg: ["0", "0"]

        master_options (str or dict):
            Driver options for the master SMU, eg: "" for real HW or simulate string

        slave_options (str or dict):
            Driver options for the slave SMUs, eg: "" for real HW or simulate string

        master_voltage_level (float):
            Voltage level to source on the master channel (V)
            eg: 1.0 → 1 V

        master_current_limit_range (float):
            Current limit range for the master channel (A)
            eg: 10e-3 → 10 mA range

        master_current_limit (float):
            Current limit for the master channel (A)
            eg: 10e-3 → 10 mA

        master_source_delay (float):
            Source delay for the master channel (s)
            eg: 50e-3 → 50 ms

        slave_voltage_levels (list of float):
            Voltage levels for each slave channel (V)
            eg: [3.0, 3.0]

        slave_current_limit_ranges (list of float):
            Current limit ranges for each slave channel (A)
            eg: [10e-3, 10e-3]

        slave_current_limits (list of float):
            Current limits for each slave channel (A)
            eg: [10e-3, 10e-3]

        slave_source_delay (float):
            Source delay for each slave channel (s)
            eg: 3e-5 → 30 µs
    """

    slave_sessions = []  # List to hold slave sessions for proper cleanup after 'with' block

    # ->Initialize Master SMU Session
    # - Opens communication with the master instrument
    # - 'with' ensures automatic cleanup of master session resources
    with nidcpower.Session(resource_name=master_resource_name, channels=master_channel, reset=False, options=master_options) as master_session:

        # -> Configure Master SMU Settings
        # - source_mode         → SINGLE_POINT
        # - output_function     → DC_VOLTAGE
        # - source_trigger_type → NONE (master triggers freely, exports events)
        # - Set voltage, current limit, and source delay
        master_session.source_mode = nidcpower.SourceMode.SINGLE_POINT
        master_session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        master_session.voltage_level = master_voltage_level
        master_session.current_limit_range = master_current_limit_range
        master_session.current_limit = master_current_limit
        master_session.source_delay = master_source_delay
        master_session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
        master_session.source_trigger_type = nidcpower.TriggerType.NONE

        source_trigger_terminal = f"/{master_resource_name}/Engine{master_channel}/SourceTrigger"
        source_complete_terminal = f"/{master_resource_name}/Engine{master_channel}/SourceCompleteEvent"
        
        # commit master session settings before configuring slaves to ensure events are properly exported
        master_session.commit()

        # -> Initialize and Configure Slave SMU Sessions
        # - Open each slave session
        # - source_mode             → SINGLE_POINT
        # - output_function         → DC_VOLTAGE
        # - source_trigger_type     → DIGITAL_EDGE (triggered by master's SourceTrigger)
        # - measure_trigger_type    → DIGITAL_EDGE (triggered by master's SourceCompleteEvent)
        # - Set source delay to near-zero so slaves are ready for the next trigger quickly
        for slave in range(len(slave_resource_names)):
            slave_sessions.append(nidcpower.Session(resource_name=slave_resource_names[slave],
                                                    channels=slave_channels[slave],
                                                    reset=False, options=slave_options))
            slave_sessions[slave].source_mode = nidcpower.SourceMode.SINGLE_POINT
            slave_sessions[slave].output_function = nidcpower.OutputFunction.DC_VOLTAGE
            slave_sessions[slave].voltage_level = slave_voltage_levels[slave]
            slave_sessions[slave].current_limit_range = slave_current_limit_ranges[slave]
            slave_sessions[slave].current_limit = slave_current_limits[slave]

            # Set the delay to 0, so that the slave(s) are ready to receive the next trigger 
            # from the master as quickly as possible.
            slave_sessions[slave].source_delay = slave_source_delay
            slave_sessions[slave].measure_when = nidcpower.MeasureWhen.ON_MEASURE_TRIGGER

            # The source trigger is the exported Source trigger from the master device.
            slave_sessions[slave].source_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE
            slave_sessions[slave].digital_edge_source_trigger_input_terminal = source_trigger_terminal

            # Measure on the master's SourceCompleteEvent to synchronize readings
            slave_sessions[slave].measure_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE
            slave_sessions[slave].digital_edge_measure_trigger_input_terminal = source_complete_terminal
            slave_sessions[slave].commit()

        # -> Initiate Slave Sessions then Master Session
        # - Slaves initiate first and wait for master's SourceTrigger
        # - Master initiates and drives the synchronized sequence
        for slave in range(len(slave_resource_names)):
            # Initiate the slave device(s)
            # Once the for loop completes, the slave device(s) will be waiting for the Source trigger.
            slave_sessions[slave].initiate()

        master_session.initiate() # master initiates and drives the synchronized sequence

        # -> Fetch Master Measurements
        # - Retrieves single-point measurement from master channel
        # - change timeout as needed based on expected source delay and measurement time
        master_meas = master_session.fetch_multiple(count=1, timeout=5)
        print(f"Master-{master_resource_name} (channel {master_channel}) Measurements: "
              f"\n- Voltage: {master_meas[0][0]:.4f} V"
              f"\n- Current: {master_meas[0][1]:.4e} A\n- In Compliance: {master_meas[0][2]}")

        # -> Fetch Slave Measurements
        # - Retrieves single-point measurement from each slave channel
        slave_measurements = []  # List to hold measurements from each slave for return at the end of the function

        # for each slave, fetch the measurement results and print them.
        for slave in range(len(slave_resource_names)):
            slave_measurements.append(slave_sessions[slave].fetch_multiple(count=1, timeout=5))
            print(f"Slave-{slave_resource_names[slave]} (Channel {slave_channels[slave]}) Measurements: "
                  f"\n- Voltage: {slave_measurements[slave][0][0]:.4f} V"
                  f"\n- Current: {slave_measurements[slave][0][1]:.4e} A"
                  f"\n- In Compliance: {slave_measurements[slave][0][2]}")


def _main(argsv):
    """Parses command-line arguments and calls example() with the parsed values."""
    parser = argparse.ArgumentParser(
        description='Single point multi-channel sync: synchronize multiple SMUs and measure.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-mrn',  '--master-resource-name',       default='PXI1Slot1',          help='Master SMU resource name')
    parser.add_argument('-mc',   '--master-channel',             default='0',                  help='Master SMU channel')
    parser.add_argument('-srn',  '--slave-resource-names',       default=['PXI1Slot2', 'PXI1Slot3'], nargs='+', help='Slave SMU resource names')
    parser.add_argument('-sc',   '--slave-channels',             default=['0', '1'],           nargs='+', help='Slave SMU channels')
    parser.add_argument('-mvl',  '--master-voltage-level',       default=1.0,   type=float,    help='Master voltage level (V)')
    parser.add_argument('-mclr', '--master-current-limit-range', default=10e-3, type=float,    help='Master current limit range (A)')
    parser.add_argument('-mcl',  '--master-current-limit',       default=10e-3, type=float,    help='Master current limit (A)')
    parser.add_argument('-msd',  '--master-source-delay',        default=50e-3, type=float,    help='Master source delay (s)')
    parser.add_argument('-svl',  '--slave-voltage-levels',       default=[3.0, 3.0],   nargs='+', type=float, help='Slave voltage levels (V)')
    parser.add_argument('-sclr', '--slave-current-limit-ranges', default=[10e-3, 10e-3], nargs='+', type=float, help='Slave current limit ranges (A)')
    parser.add_argument('-scl',  '--slave-current-limits',       default=[10e-3, 10e-3], nargs='+', type=float, help='Slave current limits (A)')
    parser.add_argument('-ssd',  '--slave-source-delay',         default=3e-5,  type=float,    help='Slave source delay (s)')
    parser.add_argument('-mop',  '--master-option-string',        default='',    type=str,      help='Master SMU driver option string, eg: "Simulate=1, DriverSetup=Model:4139; BoardType:PXIe"')
    parser.add_argument('-sop',  '--slave-option-string',         default='',    type=str,      help='Slave SMU driver option string, eg: "Simulate=1, DriverSetup=Model:4147; BoardType:PXIe"')
    args = parser.parse_args(argsv)
    example(
        master_resource_name=args.master_resource_name,
        master_channel=args.master_channel,
        slave_resource_names=args.slave_resource_names,
        slave_channels=args.slave_channels,
        master_options=args.master_option_string,
        slave_options=args.slave_option_string,
        master_voltage_level=args.master_voltage_level,
        master_current_limit_range=args.master_current_limit_range,
        master_current_limit=args.master_current_limit,
        master_source_delay=args.master_source_delay,
        slave_voltage_levels=args.slave_voltage_levels,
        slave_current_limit_ranges=args.slave_current_limit_ranges,
        slave_current_limits=args.slave_current_limits,
        slave_source_delay=args.slave_source_delay,
    )


def main():
    """Entry point — passes real CLI args to _main()."""
    _main(sys.argv[1:])


def test_example():
    """Simulated hardware test — runs example() with a virtual PXIe-4139 (no real HW needed)."""
    master_options = {'simulate': True, 'driver_setup': {'Model': '4139', 'BoardType': 'PXIe'}}
    slave_options  = {'simulate': True, 'driver_setup': {'Model': '4147', 'BoardType': 'PXIe'}}
    example(
        master_resource_name='PXI1Slot1',
        master_channel='0',
        slave_resource_names=['PXI1Slot2', 'PXI1Slot3'],
        slave_channels=['0', '0'],
        master_options=master_options,
        slave_options=slave_options,
        master_voltage_level=1.0,
        master_current_limit_range=10e-3,
        master_current_limit=10e-3,
        master_source_delay=50e-3,
        slave_voltage_levels=[3.0, 3.0],
        slave_current_limit_ranges=[10e-3, 10e-3],
        slave_current_limits=[10e-3, 10e-3],
        slave_source_delay=3e-5,
    )


def test_main():
    """Simulated CLI test — runs _main() with simulate option strings."""
    cmd_line = [
        '--master-option-string', 'Simulate=1, DriverSetup=Model:4139; BoardType:PXIe',
        '--slave-option-string',  'Simulate=1, DriverSetup=Model:4147; BoardType:PXIe',
    ]
    _main(cmd_line)


# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------
if __name__ == '__main__':
    main()
