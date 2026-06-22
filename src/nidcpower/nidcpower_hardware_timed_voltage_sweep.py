#!/usr/bin/env python3

"""NI-DCPower Hardware-Timed Voltage Sweep.

This example demonstrates how to sweep the voltage on a single channel
and display the results in a graph using Matplotlib.
This example performs a hardware-timed sweep using Sequence source mode.

The example uses the default resource name and sweep parameters.
Modify these values as needed for your measurement setup.Also
matplotlib parameters can be modified to change the size of the graph.

HOW TO RUN:
-----------
i.   From terminal (with default values):
        python nidcpower_hardware_timed_voltage_sweep.py

ii.  From terminal (with custom values):
        python nidcpower_hardware_timed_voltage_sweep.py -n "PXI1Slot1" \
            -vs 1.0 -ve 5.0 -np 10 -sd 0.005 -cl 0.01

iii. To simulate without hardware:
        PowerShell:  python nidcpower_hardware_timed_voltage_sweep.py \
            -op 'Simulate=1, DriverSetup=Model:4139; BoardType:PXIe'
        cmd.exe:     python nidcpower_hardware_timed_voltage_sweep.py \
            -op "Simulate=1, DriverSetup=Model:4139; BoardType:PXIe"

"""

# Module imports
import argparse                       # For parsing command-line arguments
import sys                            # For accessing command-line arguments via sys.argv

import matplotlib.pyplot as plt       # For plotting IV curve
from matplotlib import ticker         # For axis label formatting

import nidcpower                      # NI-DCPower instrument driver

import numpy as np                    # For numerical array operations


def example(resource_name, options, voltage_start, voltage_stop, points, source_delay, current_limit, timeout):
    """
    Perform a hardware-timed single-channel voltage sweep and display an IV curve using NI-DCPower.
    
    Args:
        resource_name (str):
            NI-DCPower device identifier (eg: "PXI1Slot1")

        options (str or dict):
            Driver options, eg: "" for real HW or simulate string for simulation

        voltage_start (float):
            Starting voltage for the sweep (V)
            eg: 1 → 1 V

        voltage_stop (float):
            Ending voltage for the sweep (V)
            eg: 5 → 5 V

        points (int):
            Number of voltage measurement points in the sweep
            eg: 10 → 10 points

        source_delay (float):
            Delay before each Source Complete Event fires (s)

        current_limit (float):
            Current limit for the sweep (A)

        timeout (float):
            Timeout for sequence completion (s)

    Returns:
        None — results are displayed as an IV curve graph
    """

    # --------------------------------------------------------
    # Step 1: Generate Voltage Sequence
    # - Clips points to a minimum of 1
    # - Calculates step voltages for the sweep sequence
    # --------------------------------------------------------
    points = np.clip(points, 1, 2147483647)  # Clip points to a minimum of 1 to avoid division by zero
    voltages = []                            # List to hold the calculated voltage levels for the sweep
    source_delays = []                       # List to hold the source delays for each voltage step

    # If only one point is requested, use the starting voltage as the single measurement point.
    # If more than one point is requested, calculate the step size and generate the voltage sequence.
    if points - 1 == 0:
        voltages.append(voltage_start)
    else:
        sequence_voltages = (voltage_stop - voltage_start) / (points - 1)
        for i in range(points):
            voltages.append((sequence_voltages * i) + voltage_start)

    # --------------------------------------------------------
    # Step 2: Set Up Graph
    # - Configures figure size and creates subplot for IV curve
    # --------------------------------------------------------
    plt.rcParams["figure.figsize"] = [7.50, 3.50] 
    plt.rcParams["figure.autolayout"] = True
    fig, ax = plt.subplots(nrows=1, figsize=(7, 9.6))

    # --------------------------------------------------------
    # Step 3: Initialize SMU Session
    # - Opens communication with the instrument
    # - 'with' ensures automatic cleanup of session resources
    # --------------------------------------------------------
    with nidcpower.Session(resource_name=resource_name, channels=0, options=options) as session:

        # ----------------------------------------------------
        # Step 4: Configure Source Settings
        # - source_mode     → SEQUENCE
        # - output_function → DC_VOLTAGE
        # - Enable autorange for voltage and current
        # - Set source delay and current limit
        # ----------------------------------------------------
        session.source_mode = nidcpower.SourceMode.SEQUENCE
        session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        session.voltage_level_autorange = True
        session.current_limit_autorange = True
        session.source_delay = source_delay
        session.current_limit = current_limit

        # ----------------------------------------------------
        # Step 5: Build Source Delays and Load Sequence
        # - Builds matching source delay array for each voltage step
        # - Loads voltage sequence into the session
        # ----------------------------------------------------
        for i in range(len(voltages)):
            source_delays.append(source_delay)

        session.set_sequence(values=voltages, source_delays=source_delays)

        # ----------------------------------------------------
        # Step 6: Initiate and Wait for Completion
        # - Starts the sequence and waits for SEQUENCE_ENGINE_DONE
        # ----------------------------------------------------
        session.initiate()
        session.wait_for_event(event_id=nidcpower.Event.SEQUENCE_ENGINE_DONE, timeout=timeout)

        # ----------------------------------------------------
        # Step 7: Fetch Measurements
        # - Retrieves all voltage and current measurements
        # - iterrate through measurements to separate voltage and current into individual lists
        # ----------------------------------------------------
        measurements = session.fetch_multiple(count=points)

        measured_voltage = []  # List to hold the measured voltage values from the sweep
        measured_current = []  # List to hold the measured current values from the sweep

        for measure in range(len(measurements)): 
            measured_voltage.append(measurements[measure][0])
            measured_current.append(measurements[measure][1])

        # ----------------------------------------------------
        # Step 8: Plot and Display Results
        # - output is disabled to prevent further sourcing after the sweep
        # - Sets window title and axis labels for the IV curve  
        # - Configures axis formatting and plots IV curve
        # - Displays the graph with plt.show()
        # ----------------------------------------------------
        session.output_enabled = False

        fig.canvas.manager.set_window_title(
            "NI-DCPower Hardware-Timed Voltage Sweep"
        )
        ax.xaxis.set_major_formatter(ticker.EngFormatter(unit="V"))
        ax.yaxis.set_major_formatter(ticker.EngFormatter(unit="A"))
        ax.set_xlabel("Voltage (V)")
        ax.set_ylabel("Current (A)")
        ax.grid()
        ax.plot(measured_voltage, measured_current)

        plt.show()


def _main(argsv):
    """Parses command-line arguments and calls example() with the parsed values."""
    parser = argparse.ArgumentParser(
        description='Hardware-timed voltage sweep: sweep voltage on a single channel and display IV curve.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-n',  '--resource-name',  default='PXI1Slot1', help='Resource name of NI SMU')
    parser.add_argument('-vs', '--voltage-start',  default=1.0,   type=float, help='Sweep start voltage (V)')
    parser.add_argument('-ve', '--voltage-stop',   default=5.0,   type=float, help='Sweep stop voltage (V)')
    parser.add_argument('-np',  '--points',        default=10,    type=int,   help='Number of measurement points')
    parser.add_argument('-sd', '--source-delay',   default=0.005, type=float, help='Source delay for each step (s)')
    parser.add_argument('-cl', '--current-limit',  default=0.01,  type=float, help='Current limit (A)')
    parser.add_argument('-op', '--option-string',  default='',    type=str,   help='Driver option string, eg: "Simulate=1, DriverSetup=Model:4139; BoardType:PXIe"')
    parser.add_argument('-t', '--timeout',         default=10.0,  type=float, help='Timeout for sequence completion (s)')
    args = parser.parse_args(argsv)
    example(
        resource_name=args.resource_name,
        options=args.option_string,
        voltage_start=args.voltage_start,
        voltage_stop=args.voltage_stop,
        points=args.points,
        source_delay=args.source_delay,
        current_limit=args.current_limit,
        timeout=args.timeout
    )


def main():
    """Entry point — passes real CLI args to _main()."""
    _main(sys.argv[1:])


def test_example():
    """Simulated hardware test — runs example() with a virtual PXIe-4139 (no real HW needed)."""
    options = {'simulate': True, 'driver_setup': {'Model': '4139', 'BoardType': 'PXIe'}}
    example('PXI1Slot1', options, 1.0, 5.0, 10, 0.005, 0.01, 10.0)


def test_main():
    """Simulated CLI test — runs _main() with simulate option string."""
    cmd_line = ['--option-string', 'Simulate=1, DriverSetup=Model:4139; BoardType:PXIe']
    _main(cmd_line)


# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------
if __name__ == '__main__':
    main()
