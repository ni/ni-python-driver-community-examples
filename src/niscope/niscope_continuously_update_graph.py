#!/usr/bin/env python3
"""NI-SCOPE - Continuously Update Graph.

This example demonstrates how to continuously read waveforms from an NI-SCOPE 
channel and display them in a graph using real-time animation with matplotlib.

The example reads waveforms continuously and updates the plot with new data
in real-time. Animation parameters can be modified to change update frequency.

HOW TO RUN:
-----------
i.   From terminal (with default values):
        python niscope_continuously_update_graph.py

ii.  From terminal (with custom values):
        python niscope_continuously_update_graph.py -n "PXIe5162" -ns 250 \
            -vr 5.0 -vc DC -sr 50000000 -rp 50.0 -ch "0" -ii 1000000 -pa 10.0

iii. To simulate without hardware:
        python niscope_continuously_update_graph.py \
            -op "Simulate=1, DriverSetup=Model:5162 (2CH); BoardType:PXIe"
"""

# Module imports
import argparse                            # For parsing command-line arguments
import sys                                 # For accessing command-line arguments via sys.argv

import matplotlib.pyplot as plt            # For plotting waveform data
import matplotlib.ticker as ticker         # For formatting axis tick labels
import matplotlib.animation as animation   # For creating animated plot updates

import niscope                             # NI-SCOPE instrument driver


def example(resource_name, options, num_samples, vertical_range, vertical_coupling, 
             sample_rate, ref_position, channels, input_impedance, probe_attenuation):
    """
    Continuously read and display waveforms from an NI-SCOPE channel using 
    real-time animated graph updates.
    
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

        vertical_coupling (str):
            Vertical coupling mode (AC, DC, or GND)
            eg: "DC" → DC coupling for full range measurement

        sample_rate (float):
            Minimum sample rate for data acquisition (samples/s)
            eg: 50000000 → 50 MHz

        ref_position (float):
            Reference position for trigger (0.0-100.0)
            eg: 50.0 → trigger at center of waveform

        channels (str):
            Channel number to read from
            eg: "0" → channel 0

        input_impedance (int):
            Input impedance in ohms (50 or 1000000)
            eg: 1000000 → 1 MΩ impedance

        probe_attenuation (float):
            Probe scale factor (1, 10, 100, etc.)
            eg: 10.0 → 10x probe attenuation
    """

    # -> Set Up Graph
    # - Configures figure size and creates subplot for waveform display
    plt.rcParams["figure.figsize"] = [7.50, 3.50]
    plt.rcParams["figure.autolayout"] = True
    fig, ax = plt.subplots()

    def update_samples(waveforms):
        """Extract waveform samples from the waveform object.
        
        Args:
            waveforms (list): List of WaveformInfo objects from niscope.read()
        
        Returns:
            list: Extracted sample values from the first waveform
        """
        samples = []
        # Iterate over waveforms[0].samples and append them to a new list
        for sample in waveforms[0].samples:
            samples.append(sample)
        return samples

    # -> Initialize Oscilloscope Session
    # - Opens communication with the instrument
    # - 'with' ensures automatic cleanup of session resources
    with niscope.Session(resource_name=resource_name, options=options) as session:

        # -> Configure Vertical Settings
        # - Configures the vertical range (voltage measurement range)
        # - Sets coupling based on user input (AC, DC, or GND)
        coupling_enum = getattr(niscope.VerticalCoupling, vertical_coupling.upper())
        session.configure_vertical(range=vertical_range, coupling=coupling_enum)

        # -> Configure Horizontal Settings
        # - Sets sample rate and number of points to acquire
        # - ref_position specifies trigger position in waveform (0.0-100.0)
        # - num_records = 1 acquires a single continuous waveform
        session.configure_horizontal_timing(min_sample_rate=sample_rate, min_num_pts=num_samples,
                                             ref_position=ref_position, num_records=1, enforce_realtime=True)

        # -> Configure Input Parameters
        # - Input impedance: 50 Ω for RF measurements or 1 MΩ for general purpose
        # - Probe attenuation: scale factor for probe (1, 10, 100, etc.)
        session.input_impedance = input_impedance
        session.probe_attenuation = probe_attenuation

        # -> Configure Trigger Settings
        # - Trigger type set to IMMEDIATE for continuous real-time acquisition
        # - Trigger level, slope, and delay configured for stable measurement
        session.trigger_type = niscope.TriggerType.IMMEDIATE
        session.trigger_level = 0.0
        session.trigger_slope = niscope.TriggerSlope.POSITIVE
        session.trigger_delay_time = 0.0

        # -> Initialize Channel List and Read First Waveform
        # - Parse comma-separated channel string into list
        # - Read initial waveform to set up plot axes and timing
        channel_list = [ch.strip() for ch in channels.split(',')]
        waveforms = session.channels[channel_list[0]].read(num_samples=num_samples)

        # Prepare time points for plotting based on the sample interval and the number of samples.
        time_points = [waveforms[0].x_increment * x for x in range(num_samples)]

        # -> Create Animated Plot
        # - Create line object for animation
        # - Configure axis formatting with engineering notation (e.g., µs, mV)
        line, = ax.plot(time_points, update_samples(waveforms=waveforms))

        ax.xaxis.set_major_formatter(ticker.EngFormatter(unit="s"))
        ax.yaxis.set_major_formatter(ticker.EngFormatter(unit="V"))
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Voltage (V)")
        ax.grid()

        def animate(frame):
            """Animation function that reads new waveforms and updates the plot.
            
            Args:
                frame (int): Current animation frame number (auto-incremented by FuncAnimation)
            
            Returns:
                tuple: Updated line object for animation rendering
            """
            # Read new waveform data from the first channel
            waveforms = session.channels[channel_list[0]].read(num_samples=num_samples)
            # Update the y-data of the line object with new waveform samples
            line.set_ydata(update_samples(waveforms=waveforms))
            return line,

        # -> Create Animation
        # - FuncAnimation continuously calls animate() at specified intervals
        # - interval=100 means update every 100 milliseconds (10 Hz)
        ani = animation.FuncAnimation(fig, animate, interval=100, blit=True, save_count=50)

        # -> Display Animated Plot
        # - Set window title and show the plot with animation loop
        fig.canvas.manager.set_window_title("NI-SCOPE Continuously Updated Waveform")
        plt.title("Waveform Graph")

        plt.show()  # Blocks execution until the plot window is closed, allowing real-time updates to be displayed.

        plt.close("all")  # Displays the plot window with the waveform data


def _main(argv):
    """Parses command-line arguments and calls example() with the parsed values."""
    parser = argparse.ArgumentParser(
        description='Continuously read and graph waveform from NI-SCOPE channel with real-time animation.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-n', '--resource-name',       default='PXIe5162',     help='Resource name of NI oscilloscope')
    parser.add_argument('-ns', '--num-samples',         default=250,   type=int,   help='Number of samples to read')
    parser.add_argument('-vr', '--vertical-range',     default=5.0,   type=float, help='Vertical range (V)')
    parser.add_argument('-vc', '--vertical-coupling',  default='DC',  type=str, choices=['AC', 'DC', 'GND'], help='Vertical coupling mode (AC, DC, or GND)')
    parser.add_argument('-sr', '--sample-rate',        default=50000000, type=float, help='Sample rate (samples/s)')
    parser.add_argument('-rp', '--ref-position',       default=50.0,  type=float, help='Reference position for trigger (0.0-100.0)')
    parser.add_argument('-ch', '--channels',            default='0',   type=str,   help='Channel to read from (comma-separated for multiple)')
    parser.add_argument('-ii', '--input-impedance',    default=1000000, type=int, choices=[50, 1000000], help='Input impedance in ohms (50 or 1000000)')
    parser.add_argument('-pa', '--probe-attenuation',  default=10.0,  type=float, help='Probe scale factor (1, 10, 100, etc.)')
    parser.add_argument('-op', '--option-string',      default='',    type=str,   help='Driver option string, eg: "Simulate=1, DriverSetup=Model:5162; BoardType:PXIe"')

    args = parser.parse_args(argv)
    example(
        resource_name=args.resource_name,
        options=args.option_string,
        num_samples=args.num_samples,
        vertical_range=args.vertical_range,
        vertical_coupling=args.vertical_coupling,
        sample_rate=args.sample_rate,
        ref_position=args.ref_position,
        channels=args.channels,
        input_impedance=args.input_impedance,
        probe_attenuation=args.probe_attenuation
    )


def main():
    """Entry point — passes real CLI args to _main()."""
    _main(sys.argv[1:])


def test_example():
    """Simulated hardware test — runs example() with a virtual PXIe-5162 (no real HW needed)."""
    plt.switch_backend("Agg")
    options = {'simulate': True, 'driver_setup': {'Model': '5162', 'BoardType': 'PXIe'}}
    example('PXIe5162', options, 250, 5.0, 'DC', 50000000, 50.0, '0', 1000000, 10.0)
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