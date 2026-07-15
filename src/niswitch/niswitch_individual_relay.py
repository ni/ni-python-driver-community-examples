#!/usr/bin/env python3
"""NI-Switch Individual Relay Control.

This example demonstrates how to control an individual relay on an NI-SWITCH
module. The switch session opens with the specified topology, applies the
desired relay action (CLOSE or OPEN) to the target relay, and waits for
debounce to confirm the relay has mechanically settled.

The example uses the default resource name and relay parameters.
Modify these values as needed for your measurement setup.

HOW TO RUN:
-----------
i.   From terminal (with default values):
        python niswitch_individual_relay.py

ii.  From terminal (with custom values):
        python niswitch_individual_relay.py \
            -n "PXI2568" -tp "2568/31-SPST" -rn "k0" -ra "CLOSE"

iii. To simulate without hardware:
        PowerShell:  python niswitch_individual_relay.py -sim
        cmd.exe:     python niswitch_individual_relay.py -sim

"""

# Module imports
import argparse    # For parsing command-line arguments
import sys         # For accessing command-line arguments via sys.argv

import niswitch    # NI-SWITCH instrument driver


def example(
    resource_name, topology, relay_name, relay_action, simulate, reset_device):
    """
    Control an individual relay on an NI-SWITCH module.

    Args:
        resource_name (str):
            NI-SWITCH device identifier
            eg: "PXI2568"

        topology (str):
            Switch topology string
            eg: "2568/31-SPST"

        relay_name (str):
            Relay identifier on the switch module
            eg: "k0"

        relay_action (str):
            Relay action to perform: "CLOSE" or "OPEN"
            eg: "CLOSE" → closes the relay

        simulate (bool):
            If True, the session runs in simulation mode (no real hardware needed)

        reset_device (bool):
            If True, resets the device at session open

    Returns:
        None — result is printed to console
    """
    # Convert relay_action string to niswitch.RelayAction enum
    action = niswitch.RelayAction[relay_action.upper()]

    # -> Open NI-SWITCH Session
    # - Opens communication with the switch module using the specified topology
    # - 'with' ensures automatic cleanup of session resources
    with niswitch.Session(
        resource_name=resource_name,
        topology=topology,
        simulate=simulate,
        reset_device=reset_device,
    ) as session:

        # -> Control Relay
        # - Applies the specified relay action (CLOSE or OPEN) to the target relay
        session.relay_control(relay_name, action)

        # -> Wait for Debounce
        # - Waits until the relay has mechanically settled after the action
        session.wait_for_debounce()

        # - Print relay action result to console
        print(f"Relay '{relay_name}': {relay_action.upper()} action completed.")


def _main(argsv):
    """Parses command-line arguments and calls example() with the parsed values."""
    parser = argparse.ArgumentParser(
        description='NI-SWITCH Individual Relay Control: close or open a relay on a switch module.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-n',  '--resource-name',    default='PXI2568',        help='NI-SWITCH device resource name')
    parser.add_argument('-tp',  '--topology',        default='2568/31-SPST',  help='Switch topology string')
    parser.add_argument('-rn',  '--relay-name',      default='k0',            help='Relay identifier on the switch module')
    parser.add_argument('-ra',  '--relay-action',    default='CLOSE',         choices=['CLOSE', 'OPEN'], help='Relay action to perform')
    parser.add_argument('-sim', '--simulate',       action='store_true', default=False, help='Run in simulation mode (no hardware required)')
    parser.add_argument('-rst', '--reset-device',   action='store_true', default=False, help='Reset device at session open')
    args = parser.parse_args(argsv)
    example(
        resource_name=args.resource_name,
        topology=args.topology,
        relay_name=args.relay_name,
        relay_action=args.relay_action,
        simulate=args.simulate,
        reset_device=args.reset_device,
    )


def main():
    """Entry point — passes real CLI args to _main()."""
    _main(sys.argv[1:])


def test_example():
    """Simulated hardware test — runs example() with virtual NI-2568 switch (no real HW needed)."""
    example(
        resource_name='PXI2568',
        topology='2568/31-SPST',
        relay_name='k0',
        relay_action='CLOSE',
        simulate=True,
        reset_device=False,
    )


def test_main():
    """Simulated CLI test — runs _main() with simulate flag."""
    cmd_line = ['--simulate']
    _main(cmd_line)


# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------
if __name__ == '__main__':
    main()
