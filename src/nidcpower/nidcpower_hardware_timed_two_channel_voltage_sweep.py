#!/usr/bin/env python3
"""NI-DCPower Hardware-Timed Two-Channel Voltage Sweep (IV Curve).

This example demonstrates how to set up a hardware-timed,
two-channel nested voltage sweep and display the results in a graph (IV Curve).

Use this example to produce the characteristic curves of a FET transistor.
It can be easily adapted to test a BJT by performing a current sweep instead
of a voltage sweep.This example performs a hardware-timed sweep
(with triggers and events) using Sequence source mode.

When the plot displays after code execution, you can click on each plot in the
right-hand corner of the graph to enable/disable its visibility.

The example uses the default resource names, channel numbers, and sweep
parameters.Modify these values as needed for your measurement setup.

HOW TO RUN:
-----------
i.   From terminal (with default values):
        python nidcpower_hardware_timed_two_channel_voltage_sweep.py

ii.  From terminal (with custom values):
        python nidcpower_hardware_timed_two_channel_voltage_sweep.py \
            -grn "PXI1Slot1" -gc "0" -drn "PXI1Slot2" -dc "0" \
            -gvs 3.5 -gve 3.9 -dvs 1.0 -dve 5.0 -pl 5 -p 10

iii. To simulate without hardware:
        PowerShell:  python nidcpower_hardware_timed_two_channel_voltage_sweep.py \
            -op 'Simulate=1, DriverSetup=Model:4139; BoardType:PXIe'
        cmd.exe:     python nidcpower_hardware_timed_two_channel_voltage_sweep.py \
            -op "Simulate=1, DriverSetup=Model:4139; BoardType:PXIe"

"""

# Module imports
import argparse                       # For parsing command-line arguments
import sys                            # For accessing command-line arguments via sys.argv

from matplotlib import pyplot as plt  # For plotting IV curve
from matplotlib import ticker         # For axis label formatting

import nidcpower                      # NI-DCPower instrument driver

import numpy as np                    # For numerical array operations


def example(
    gate_resource_name, gate_channel, drain_resource_name, drain_channel, options, gate_voltage_start,
    gate_voltage_stop, drain_voltage_start, drain_voltage_stop, plots, points, gate_source_delay,
    gate_current_limit, drain_source_delay, drain_current_limit):
    """
    Perform a hardware-timed two-channel voltage sweep and display an IV curve using NI-DCPower.

    Args:
        gate_resource_name (str):
            NI-DCPower device identifier for the gate SMU (eg: "PXI1Slot1")

        gate_channel (str):
            Channel number for the gate SMU (eg: "0")

        drain_resource_name (str):
            NI-DCPower device identifier for the drain SMU (eg: "PXI1Slot2")

        drain_channel (str):
            Channel number for the drain SMU (eg: "0")

        options (str or dict):
            Driver options, eg: "" for real HW or simulate string for simulation

        gate_voltage_start (float):
            Starting gate voltage for the sweep (V)
            eg: 3.5 → 3.5 V

        gate_voltage_stop (float):
            Ending gate voltage for the sweep (V)
            eg: 3.9 → 3.9 V

        drain_voltage_start (float):
            Starting drain voltage for the sweep (V)
            eg: 1 → 1 V

        drain_voltage_stop (float):
            Ending drain voltage for the sweep (V)
            eg: 5 → 5 V

        plots (int):
            Number of gate voltage steps (IV curves to generate)
            eg: 5 → 5 curves

        points (int):
            Number of drain voltage measurement points per curve
            eg: 10 → 10 points per curve

        gate_source_delay (float):
            Source delay for the gate channel (s)
            eg: 0.003 → 3 ms

        gate_current_limit (float):
            Current limit for the gate channel (A)
            eg: 0.01 → 10 mA

        drain_source_delay (float):
            Source delay for the drain channel (s)
            eg: 0.005 → 5 ms

        drain_current_limit (float):
            Current limit for the drain channel (A)
            eg: 0.01 → 10 mA

    Returns:
        None — results are printed to console and displayed as an interactive IV curve graph
    """

    # -> Generate Voltage Sequences
    # - Clips plots/points to a minimum of 1
    # - Generates step voltages for the gate channel and drain channel SMU
    plots = np.clip(plots, 1, 2147483647)
    points = np.clip(points, 1, 2147483647)

    gate_sequence = []
    drain_sequence = []
    source_delays = []

    if plots - 1 == 0:
        gate_sequence.append(gate_voltage_start)
    else:
        voltages_0 = (gate_voltage_stop - gate_voltage_start) / (plots - 1)
        for i in range(plots):
            gate_sequence.append((voltages_0 * i) + gate_voltage_start)

    if points - 1 == 0:
        drain_sequence.append(drain_voltage_start)
    else:
        voltages_1 = (drain_voltage_stop - drain_voltage_start) / (points - 1)
        for i in range(points):
            drain_sequence.append((voltages_1 * i) + drain_voltage_start)

    # -> Set Up Graph
    # - Configures figure size and creates subplot for IV curve
    plt.rcParams["figure.figsize"] = [7.50, 3.50]
    plt.rcParams["figure.autolayout"] = True
    fig, ax = plt.subplots(nrows=1, figsize=(7, 9.6))

    # -> Initialize Both SMU Sessions
    # - Opens communication with gate and drain instruments
    # - 'with' ensures automatic cleanup of session resources
    with (
        nidcpower.Session(resource_name=f"{gate_resource_name}/{gate_channel}", options=options) as gate_session,
        nidcpower.Session(resource_name=f"{drain_resource_name}/{drain_channel}", options=options) as drain_session,
    ):

        # -> Configure Gate Channel Settings
        # - source_mode         → SEQUENCE
        # - output_function     → DC_VOLTAGE
        # - source_trigger_type → DIGITAL_EDGE (triggered by drain's SequenceIterationCompleteEvent)
        # - Build source delay array and load sequence
        gate_session.source_mode = nidcpower.SourceMode.SEQUENCE
        gate_session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        gate_session.voltage_level_autorange = True
        gate_session.current_limit_autorange = True
        gate_session.source_delay = gate_source_delay
        gate_session.current_limit = gate_current_limit

        for i in range(len(gate_sequence)):
            source_delays.append(gate_source_delay)

        gate_session.set_sequence(values=gate_sequence, source_delays=source_delays)

        gate_session.source_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE
        gate_session.digital_edge_source_trigger_input_terminal = (
            f"/{drain_resource_name}/Engine{drain_channel}/SequenceIterationCompleteEvent"
        )

        # Commit gate session configuration to ensure it is ready to receive 
        # the trigger from the drain channel
        gate_session.commit()

        # -> Configure Drain Channel Settings
        # - source_mode                    → SEQUENCE
        # - output_function                → DC_VOLTAGE
        # - start_trigger_type             → DIGITAL_EDGE (triggered by gate's MeasureCompleteEvent)
        # - sequence_advance_trigger_type  → DIGITAL_EDGE (advances on gate's MeasureCompleteEvent)
        # - Build source delay array and load sequence
        drain_session.source_mode = nidcpower.SourceMode.SEQUENCE
        drain_session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        drain_session.voltage_level_autorange = True
        drain_session.current_limit_autorange = True
        drain_session.source_delay = drain_source_delay
        drain_session.current_limit = drain_current_limit

        source_delays = []
        for i in range(len(drain_sequence)):
            source_delays.append(drain_source_delay)

        drain_session.set_sequence(values=drain_sequence, source_delays=source_delays)

        drain_session.start_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE
        drain_session.digital_edge_start_trigger_input_terminal = (
            f"/{gate_resource_name}/Engine{gate_channel}/MeasureCompleteEvent"
        )
        drain_session.sequence_advance_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE
        drain_session.digital_edge_sequence_advance_trigger_input_terminal = (
            f"/{gate_resource_name}/Engine{gate_channel}/MeasureCompleteEvent"
        )
        drain_session.sequence_loop_count = plots

        # Commit drain session configuration to ensure it is ready to receive 
        # the trigger from the gate channel
        drain_session.commit()

        # -> Initiate and Wait for Completion
        # - Drain initiates first (waiting for gate's trigger)
        # - Gate initiates and drives the sweep sequence
        # - Wait until sequence engine completes (timeout: 15 s)
        drain_session.initiate()
        gate_session.initiate()
        drain_session.wait_for_event(event_id=nidcpower.Event.SEQUENCE_ENGINE_DONE, timeout=15)

        # -> Fetch Measurements
        # - Fetches gate measurements (one per plot)
        # - Fetches drain measurements (points per plot)
        gate_measurements = gate_session.fetch_multiple(count=plots, timeout=10)

        drain_measurements = []
        for plot in range(len(gate_measurements)):
            drain_measurements.append(drain_session.fetch_multiple(count=points, timeout=10))

        # -> Print Results and Plot IV Curves
        # - Prints formatted table of gate voltage, drain current, drain voltage
        # - Plots each IV curve with gate voltage as legend label
        # - Disables output on both SMUs after measurement
        drain_voltages = []
        drain_currents = []

        line_format = '{:<18} {:<18} {:<18}'
        print(line_format.format('Gate Voltage (V)', 'Drain Current (A)', 'Drain Voltage (V)'))

        for plot in range(len(gate_measurements)):
            for point in range(len(drain_measurements[0])):
                drain_voltages.append(drain_measurements[plot][point].voltage)
                drain_currents.append(drain_measurements[plot][point].current)
                print(line_format.format(
                    "{:.3f}".format(gate_measurements[plot][0]),
                    "{:.3e}".format(drain_measurements[plot][point].current),
                    "{:.3f}".format(drain_measurements[plot][point].voltage),
                ))

            ax.plot(drain_voltages, drain_currents, marker='o', label=f"{gate_measurements[plot].voltage:.3f} V")
            drain_voltages = []
            drain_currents = []

        gate_session.output_enabled = False
        drain_session.output_enabled = False

        # -> Configure Interactive Graph Display
        # - Adds legend with clickable toggle for each IV curve
        # - Connects pick event to show/hide individual plots
        lines = ax.get_lines()
        leg = ax.legend(fancybox=True, shadow=True)
        lined = {}

        for legline, origline in zip(leg.get_lines(), lines):
            legline.set_picker(True)
            legline.set_pickradius(3)
            lined[legline] = origline

        def on_pick(event):
            """On the pick event, find the original line corresponding to the legend proxy line, and toggle its visibility."""
            legline = event.artist
            origline = lined[legline]
            visible = not origline.get_visible()
            origline.set_visible(visible)
            legline.set_alpha(1.0 if visible else 0.2)
            fig.canvas.draw()

        ax.xaxis.set_major_formatter(ticker.EngFormatter(unit="V"))
        ax.yaxis.set_major_formatter(ticker.EngFormatter(unit="A"))
        ax.set_xlabel('Voltage (V)')
        ax.set_ylabel('Current (A)')
        ax.grid()
        # Connects 'pick_event' to on_pick function to hide and display each plot by clicking on their corresponding legend color:
        fig.canvas.mpl_connect('pick_event', on_pick)
        fig.suptitle("Current (Amps) vs Voltage (Volts)")

        fig.canvas.manager.set_window_title(
            "NI-DCPower Hardware-Timed two channel Voltage Sweep"
        )  # Sets the window title for the graph display

        plt.show()  # Display the plot window

        plt.close(fig)  # Close the figure to free up memory after the plot window is closed


def _main(argsv):
    """Parses command-line arguments and calls example() with the parsed values."""
    parser = argparse.ArgumentParser(
        description='Hardware-timed two-channel voltage sweep: generate IV curves for FET characterisation.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-grn', '--gate-resource-name',  default='PXI1Slot1', help='Gate SMU resource name')
    parser.add_argument('-gc',  '--gate-channel',        default='0',         help='Gate SMU channel')
    parser.add_argument('-drn', '--drain-resource-name', default='PXI1Slot2', help='Drain SMU resource name')
    parser.add_argument('-dc',  '--drain-channel',       default='0',         help='Drain SMU channel')
    parser.add_argument('-gvs', '--gate-voltage-start',  default=3.5,   type=float, help='Gate sweep start voltage (V)')
    parser.add_argument('-gve', '--gate-voltage-stop',   default=3.9,   type=float, help='Gate sweep stop voltage (V)')
    parser.add_argument('-dvs', '--drain-voltage-start', default=1.0,   type=float, help='Drain sweep start voltage (V)')
    parser.add_argument('-dve', '--drain-voltage-stop',  default=5.0,   type=float, help='Drain sweep stop voltage (V)')
    parser.add_argument('-pl',  '--plots',               default=5,     type=int,   help='Number of gate voltage steps (IV curves)')
    parser.add_argument('-p',   '--points',              default=10,    type=int,   help='Number of drain voltage points per curve')
    parser.add_argument('-gsd', '--gate-source-delay',   default=0.003, type=float, help='Gate source delay (s)')
    parser.add_argument('-gcl', '--gate-current-limit',  default=0.01,  type=float, help='Gate current limit (A)')
    parser.add_argument('-dsd', '--drain-source-delay',  default=0.005, type=float, help='Drain source delay (s)')
    parser.add_argument('-dcl', '--drain-current-limit', default=0.01,  type=float, help='Drain current limit (A)')
    parser.add_argument('-op',  '--option-string',       default='',    type=str,   help='Driver option string, eg: "Simulate=1, DriverSetup=Model:4139; BoardType:PXIe"')
    args = parser.parse_args(argsv)
    example(
        gate_resource_name=args.gate_resource_name,
        gate_channel=args.gate_channel,
        drain_resource_name=args.drain_resource_name,
        drain_channel=args.drain_channel,
        options=args.option_string,
        gate_voltage_start=args.gate_voltage_start,
        gate_voltage_stop=args.gate_voltage_stop,
        drain_voltage_start=args.drain_voltage_start,
        drain_voltage_stop=args.drain_voltage_stop,
        plots=args.plots,
        points=args.points,
        gate_source_delay=args.gate_source_delay,
        gate_current_limit=args.gate_current_limit,
        drain_source_delay=args.drain_source_delay,
        drain_current_limit=args.drain_current_limit,
    )


def main():
    """Entry point — passes real CLI args to _main()."""
    _main(sys.argv[1:])


def test_example():
    """Simulated hardware test — runs example() with a virtual PXIe-4139 (no real HW needed)."""
    plt.switch_backend('Agg')
    options = {'simulate': True, 'driver_setup': {'Model': '4139', 'BoardType': 'PXIe'}}
    example(
        gate_resource_name='PXI1Slot1',
        gate_channel='0',
        drain_resource_name='PXI1Slot2',
        drain_channel='0',
        options=options,
        gate_voltage_start=3.5,
        gate_voltage_stop=3.9,
        drain_voltage_start=1.0,
        drain_voltage_stop=5.0,
        plots=5,
        points=10,
        gate_source_delay=0.003,
        gate_current_limit=0.01,
        drain_source_delay=0.005,
        drain_current_limit=0.01,
    )

    plt.close('all') # Close all figures


def test_main():
    """Simulated CLI test — runs _main() with simulate option string."""
    plt.switch_backend('Agg')
    cmd_line = ['--option-string', 'Simulate=1, DriverSetup=Model:4139; BoardType:PXIe']
    _main(cmd_line)
    plt.close('all')


# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------
if __name__ == '__main__':
    main()
