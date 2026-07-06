#!/usr/bin/env python3
"""NI-SCOPE - Read and Plot Waveform.

This example demonstrates how to read waveforms from an NI-SCOPE channel
and display them in a plot using the matplotlib library.

The example reads waveforms from a single channel with configurable parameters.
Matplotlib parameters can be modified to change the size and appearance of the plot.

HOW TO RUN:
-----------
i.   From terminal (with default values):
        python niscope_read_and_plot_waveform.py

ii.  From terminal (with custom values):
        python niscope_read_and_plot_waveform.py -n "PXIe5162" -ns 500 \
            -vr 10.0 -sr 50000000 -ch "0" -vc DC -ref 50.0 -pa 10.0 -ii 1000000

iii. To simulate without hardware:
        python niscope_read_and_plot_waveform.py \
            -op "Simulate=1, DriverSetup=Model:5162 (2CH); BoardType:PXIe"

"""

# Module imports
import argparse                       # For parsing command-line arguments
import sys                            # For accessing command-line arguments via sys.argv

import matplotlib.pyplot as plt       # For plotting waveform data
from matplotlib import ticker         # For axis label formatting

import niscope                        # NI-SCOPE instrument driver


def example(resource_name, options, num_samples, vertical_range, sample_rate, channel, vertical_coupling, ref_position, probe_attenuation, input_impedance):
    """
    Read and display a waveform from an NI-SCOPE channel using a plot.
    
    Args:
        resource_name (str):
            NI-SCOPE device identifier (eg: "PXIe5162")

        options (str or dict):
            Driver options, eg: "" for real HW or simulate string for simulation

        num_samples (int):
            Number of samples to read from the waveform
            eg: 250 → 250 samples

        vertical_range (float):
            Vertical range setting for the oscilloscope (V)
            eg: 5.0 → ±5 V range

        sample_rate (float):
            Minimum sample rate for data acquisition (samples/s)
            eg: 50000000 → 50 MHz

        channel (str):
            Channel number to read from
            eg: "1" → channel 1

        vertical_coupling (str):
            Vertical coupling mode (AC or DC)
            eg: "AC" → AC coupling to filter DC component

        ref_position (float):
            Reference position for trigger (0.0-100.0)
            eg: 50.0 → trigger at center of waveform

        probe_attenuation (float):
            Probe attenuation ratio (V/V)
            eg: 1.0 → 1X attenuation, 10.0 → 10X attenuation

        input_impedance (int):
            Input impedance in ohms (50 or 1000000)
            eg: 1000000 → 1 MΩ impedance
    """

    # -> Set Up Plot
    # - Configures figure size and creates subplot for waveform display
    plt.rcParams["figure.figsize"] = [7.50, 3.50]
    plt.rcParams["figure.autolayout"] = True
    fig, ax = plt.subplots()

    samples = []  # List where samples will be stored for plotting

    # -> Initialize Oscilloscope Session
    # - Opens communication with the instrument
    # - 'with' ensures automatic cleanup of session resources
    with niscope.Session(resource_name=resource_name, options=options) as session:

        # -> Configure Vertical Settings
        # - Configures the vertical range (voltage measurement range)
        # - Sets coupling based on user input (AC to filter DC, or DC for full range)
        # - Sets probe attenuation for the channel
        # - Configures input impedance (50 Ω for RF or 1 MΩ for general purpose)
        coupling = niscope.VerticalCoupling.AC if vertical_coupling.upper() == 'AC' else niscope.VerticalCoupling.DC
        session.configure_vertical(range=vertical_range, coupling=coupling)
        session.channels[channel].probe_attenuation = probe_attenuation
        session.input_impedance = input_impedance

        # -> Configure Horizontal Settings
        # - Sets sample rate and number of points to acquire
        # - ref_position specifies trigger position in waveform (0.0-100.0)
        # - num_records = 1 acquires a single continuous waveform
        session.configure_horizontal_timing(min_sample_rate=sample_rate, min_num_pts=num_samples,
                                            ref_position=ref_position, num_records=1, enforce_realtime=True)

        # -> Read Waveform Data
        # - The read() method acquires waveform data from the specified channel
        # - Returns a list of WaveformInfo objects with samples and timing information
        waveforms = session.channels[channel].read(num_samples=num_samples)

        # -> Extract Sample Data
        # - Iterates through waveform samples and stores them in a list
        # - waveforms[0] corresponds to the first (and typically only) waveform in the list
        for sample in waveforms[0].samples:
            samples.append(sample)

        # -> Calculate Time Axis
        # - x_increment is the delta-t (time interval between samples)
        # - Multiplying by sample index creates the time axis for plotting
        time_points = [waveforms[0].x_increment * x for x in range(num_samples)]

        # -> Plot and Display Results
        # - Configures axis formatting with engineering notation (e.g., µs, mV)
        # - Sets axis labels and enables grid for readability
        # - Plots and displays the waveform plot
        fig.canvas.manager.set_window_title("NI-SCOPE Waveform Plot")
        ax.xaxis.set_major_formatter(ticker.EngFormatter(unit="s"))
        ax.yaxis.set_major_formatter(ticker.EngFormatter(unit="V"))
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Voltage (V)")
        ax.grid()
        ax.plot(time_points, samples)
 
        plt.show() # Displays the plot window with the waveform data

        plt.close("all") # Closes all open plot windows to free resources


def _main(argsv):
    """Parses command-line arguments and calls example() with the parsed values."""
    parser = argparse.ArgumentParser(
        description='Read and plot waveform from NI-SCOPE channel.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-n', '--resource-name',  default='PXIe5162',     help='Resource name of NI oscilloscope')
    parser.add_argument('-ns', '--num-samples',    default=250,   type=int,   help='Number of samples to read')
    parser.add_argument('-vr', '--vertical-range', default=5.0,  type=float, help='Vertical range (V)')
    parser.add_argument('-sr', '--sample-rate',   default=50000000, type=float, help='Sample rate (samples/s)')
    parser.add_argument('-ch', '--channel',        default='0',   type=str,   help='Channel to read from')
    parser.add_argument('-vc', '--vertical-coupling', default='DC', type=str, choices=['AC', 'DC', 'GND'], help='Vertical coupling mode (AC or DC)')
    parser.add_argument('-ref', '--ref-position',  default=50.0,  type=float, help='Reference position for trigger (0.0-100.0)')
    parser.add_argument('-pa', '--probe-attenuation', default=10.0, type=float, help='Probe attenuation ratio (V/V) - eg: 1.0 for 1X, 10.0 for 10X')
    parser.add_argument('-ii', '--input-impedance', default=1000000, type=int, choices=[50, 1000000], help='Input impedance in ohms (50 or 1000000)')
    parser.add_argument('-op', '--option-string', default='',    type=str,   help='Driver option string, eg: "Simulate=1, DriverSetup=Model:5162; BoardType:PXIe"')
    
    args = parser.parse_args(argsv)
    example(
        resource_name=args.resource_name,
        options=args.option_string,
        num_samples=args.num_samples,
        vertical_range=args.vertical_range,
        sample_rate=args.sample_rate,
        channel=args.channel,
        vertical_coupling=args.vertical_coupling,
        ref_position=args.ref_position,
        probe_attenuation=args.probe_attenuation,
        input_impedance=args.input_impedance
    )


def main():
    """Entry point — passes real CLI args to _main()."""
    _main(sys.argv[1:])


def test_example():
    """Simulated hardware test — runs example() with a virtual PXIe-5162 (no real HW needed)."""
    plt.switch_backend("Agg")
    options = {'simulate': True, 'driver_setup': {'Model': '5162', 'BoardType': 'PXIe'}}
    example('PXIe5162', options, 250, 5.0, 50000000, '0', 'DC', 50.0, 10.0, 1000000)
    plt.close("all")  # Close all figures to free up memory after the test


def test_main():
    """Simulated CLI test — runs _main() with simulate option string."""
    plt.switch_backend("Agg")
    cmd_line = ['--option-string', 'Simulate=1, DriverSetup=Model:5162; BoardType:PXIe']
    _main(cmd_line)
    plt.close("all")  # Close all figures to free up memory after the test


# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------
if __name__ == '__main__':
    main()
