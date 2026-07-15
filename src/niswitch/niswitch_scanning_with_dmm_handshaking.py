#!/usr/bin/env python3
"""NI-Switch Scanning with DMM Handshaking.

This example demonstrates how to scan a series of channels on an NI-SWITCH
module and take measurements with an NI-DMM using TTL handshaking.

The switch and DMM are synchronized via two TTL trigger lines:
  - Switch ScanAdvancedOutput (TTL1)  →  DMM trigger input   (PXI_TRIG1)
  - DMM MeasurementCompleteDest (TTL0) →  Switch trigger input (TTL0)

Each time the switch connects a new path it pulses TTL1, triggering the DMM
to measure. When the DMM finishes, it pulses TTL0, advancing the switch to
the next scan step.

The example uses the default resource names and measurement parameters.
Modify these values as needed for your measurement setup.

HOW TO RUN:
-----------
i.   From terminal (with default values):
        python niswitch_scanning_with_dmm_handshaking.py

ii.  From terminal (with custom values):
        python niswitch_scanning_with_dmm_handshaking.py \
            -swrn "PXI2568" -swtp "2568/31-SPST" -dmmrn "PXI4081" \
            -sl "ch0->com0;" -sf 5 -dr 10.0 -dres 1e-3

iii. To simulate without hardware:
        PowerShell:  python niswitch_scanning_with_dmm_handshaking.py \
            -sim -dop 'Simulate=1, DriverSetup=Model:4081'
        cmd.exe:     python niswitch_scanning_with_dmm_handshaking.py \
            -sim -dop "Simulate=1, DriverSetup=Model:4081"

"""

# Module imports
import argparse    # For parsing command-line arguments
import sys         # For accessing command-line arguments via sys.argv

import nidmm       # NI-DMM instrument driver

import niswitch    # NI-SWITCH instrument driver


def example( switch_resource_name, switch_topology, dmm_resource_name, dmm_options,
    scan_list, samples_to_fetch, dmm_range, dmm_resolution,
    continuous_scan, switch_simulate, reset_device):
    """
    Scan channels on an NI-SWITCH module and take measurements with an NI-DMM
    using TTL handshaking.

    Handshaking sequence:
        Switch (TTL1) → triggers DMM to measure → DMM (TTL0) → advances switch scan

    Args:
        switch_resource_name (str):
            NI-SWITCH device identifier
            eg: "PXI2568"

        switch_topology (str):
            Switch topology string
            eg: "2568/31-SPST"

        dmm_resource_name (str):
            NI-DMM device identifier
            eg: "PXI4081"

        dmm_options (str or dict):
            DMM driver options, eg: "" for real HW or simulate string for simulation

        scan_list (str):
            Semicolon-delimited list of channel connections to scan
            eg: "ch0->com0;" → connect ch0 to com0

        samples_to_fetch (int):
            Minimum number of measurement samples to fetch from the DMM
            eg: 5 → fetch at least 5 samples

        dmm_range (float):
            DMM DC voltage measurement range (V)
            eg: 10.0 → ±10 V range

        dmm_resolution (float):
            DMM measurement resolution (V)
            eg: 1e-3 → 1 mV resolution

        continuous_scan (bool):
            If True, the switch scan loops continuously until aborted
            If False, the scan completes a single pass and stops

        switch_simulate (bool):
            If True, the switch session runs in simulation mode (no real hardware needed)

        reset_device (bool):
            If True, resets the switch device at session open

    Returns:
        None — results are printed to console
    """

    # -> Open NI-SWITCH Session
    # - Opens communication with the switch module using the specified topology
    # - 'with' ensures automatic cleanup of session resources
    with niswitch.Session(
        resource_name=switch_resource_name,
        topology=switch_topology,
        simulate=switch_simulate,
        reset_device=reset_device,
    ) as switch_session:

        # -> Configure Switch Scan Settings
        # - trigger_input       → TTL0: switch advances when DMM signals MeasurementComplete
        # - scan_advanced_output → TTL1: switch pulses TTL1 after each path connection,
        #                          triggering the DMM to start a measurement
        # - continuous_scan     → controls whether the scan loops or runs once
        # - scan_list           → defines the channel connections to scan through
        switch_session.trigger_input = niswitch.TriggerInput.TTL0
        switch_session.scan_advanced_output = niswitch.ScanAdvancedOutput.TTL1
        switch_session.continuous_scan = continuous_scan
        switch_session.scan_list = scan_list

        # Commit switch settings before opening the DMM session
        # (ensures trigger routing is applied before the DMM is armed)
        switch_session.commit()

        # -> Open NI-DMM Session
        # - Opens communication with the DMM
        # - reset_device=False: preserves any existing DMM configuration
        # - 'with' ensures automatic cleanup of session resources
        with nidmm.Session(
            resource_name=dmm_resource_name,
            id_query=False,
            reset_device=False,
            options=dmm_options,
        ) as dmm_session:

            # -> Configure DMM Measurement Settings
            # - DC voltage measurement with specified range and resolution
            dmm_session.configure_measurement_absolute(
                measurement_function=nidmm.Function.DC_VOLTS,
                range=dmm_range,
                resolution_absolute=dmm_resolution,
            )

            # -> Configure DMM Trigger Settings
            # - PXI_TRIG1: DMM waits for Switch ScanAdvancedOutput (TTL1) before each measurement
            # - Trigger slope set to Falling (raw attribute 1250334, value 0=Falling / 1=Rising)
            dmm_session.configure_trigger(trigger_source=nidmm.TriggerSource.PXI_TRIG1)
            dmm_session._set_attribute_vi_int32(attribute_id=1250334, attribute_value=0)   # Trigger slope: Falling

            # -> Configure DMM Multi-Point Acquisition
            # - sample_count=0   → continuous acquisition (DMM keeps measuring until abort)
            # - IMMEDIATE sample trigger: DMM samples immediately after each trigger
            dmm_session.configure_multi_point(
                trigger_count=1,
                sample_count=0,
                sample_trigger=nidmm.SampleTrigger.IMMEDIATE,
            )
            dmm_session._set_attribute_vi_int32(attribute_id=1150010, attribute_value=0)   # Raw attribute: multi-point config

            # -> Configure DMM Measurement Complete Destination
            # - PXI_TRIG0: DMM pulses TTL0 when each measurement is complete,
            #   signalling the switch to advance to the next scan step
            dmm_session.meas_complete_dest = nidmm.MeasurementCompleteDest.PXI_TRIG0
            dmm_session._set_attribute_vi_int32(attribute_id=1150002, attribute_value=0)   # Raw attribute: meas complete dest config

            # -> Initiate Sessions
            # - DMM initiates first (arms and waits for the first TTL1 trigger from switch)
            # - Switch initiates after, begins scanning and pulsing TTL1
            dmm_session.initiate()
            switch_session.initiate()

            # -> Fetch and Print Results
            # - Read current DMM acquisition status (samples acquired so far)
            # - Fetch at least samples_to_fetch, or however many the DMM has ready
            dmm_status = dmm_session.read_status()
            print("DMM Status:    ", dmm_status)

            measurement = dmm_session.fetch_multi_point(
                array_size=max(dmm_status[0], samples_to_fetch),
                maximum_time=5000,
            )
            print("Measurements:  ", measurement)


def _main(argsv):
    """Parses command-line arguments and calls example() with the parsed values."""
    parser = argparse.ArgumentParser(
        description='NI-SWITCH Scanning with DMM Handshaking: scan channels and measure using synchronized TTL triggers.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-swrn', '--switch-resource-name',   default='PXI2568',         help='NI-SWITCH device resource name')
    parser.add_argument('-swtp', '--switch-topology',        default='2568/31-SPST',   help='Switch topology string')
    parser.add_argument('-dmmrn','--dmm-resource-name',      default='PXI4081',        help='NI-DMM device resource name')
    parser.add_argument('-sl',   '--scan-list',              default='ch0->com0;',     help='Semicolon-delimited scan list (eg: "ch0->com0;")')
    parser.add_argument('-sf',   '--samples-to-fetch',       default=5,    type=int,   help='Minimum number of DMM samples to fetch')
    parser.add_argument('-dr',   '--dmm-range',              default=10.0, type=float, help='DMM DC voltage measurement range (V)')
    parser.add_argument('-dres', '--dmm-resolution',         default=1e-3, type=float, help='DMM measurement resolution (V)')
    parser.add_argument('-cs',  '--continuous-scan',   action='store_true', default=False, help='Enable continuous scan (loops until aborted; default: single pass)')
    parser.add_argument('-sim', '--switch-simulate',   action='store_true', default=False, help='Run switch in simulation mode (no hardware required)')
    parser.add_argument('-rst', '--reset-device',      action='store_true', default=False, help='Reset switch device at session open')
    parser.add_argument('-dop', '--dmm-option-string', default='',   type=str,             help='DMM driver option string, eg: "Simulate=1, DriverSetup=Model:4081"')
    args = parser.parse_args(argsv)
    example(
        switch_resource_name=args.switch_resource_name,
        switch_topology=args.switch_topology,
        dmm_resource_name=args.dmm_resource_name,
        dmm_options=args.dmm_option_string,
        scan_list=args.scan_list,
        samples_to_fetch=args.samples_to_fetch,
        dmm_range=args.dmm_range,
        dmm_resolution=args.dmm_resolution,
        continuous_scan=args.continuous_scan,
        switch_simulate=args.switch_simulate,
        reset_device=args.reset_device,
    )


def main():
    """Entry point — passes real CLI args to _main()."""
    _main(sys.argv[1:])


def test_example():
    """Simulated hardware test — runs example() with virtual NI-2568 switch and NI-4081 DMM (no real HW needed)."""
    dmm_options = {'simulate': True, 'driver_setup': {'Model': '4081'}}
    example(
        switch_resource_name='PXI2568',
        switch_topology='2568/31-SPST',
        dmm_resource_name='DMM',
        dmm_options=dmm_options,
        scan_list='ch0->com0;',
        samples_to_fetch=5,
        dmm_range=10.0,
        dmm_resolution=1e-3,
        continuous_scan=True,
        switch_simulate=True,
        reset_device=False,
    )


def test_main():
    """Simulated CLI test — runs _main() with simulate flags."""
    cmd_line = [
        '--switch-simulate',
        '--continuous-scan',
        '--dmm-option-string', 'Simulate=1, DriverSetup=Model:4081',
    ]
    _main(cmd_line)


# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------
if __name__ == '__main__':
    main()
