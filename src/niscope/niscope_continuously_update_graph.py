#!/usr/bin/env python3
"""NI-SCOPE - Continuously Update Graph

This example demonstrates how to continuously read a waveform from 
NI oscilloscope, plot it using matplotlib, and update the plot with
new sets of data in real-time using animation.

HOW TO RUN:
-----------
i.   From terminal (with default values):
        python niscope_continuously_update_graph.py
 
ii.  From terminal (with custom oscilloscope configuration):
        python niscope_continuously_update_graph.py \
            -n "PXIe5162" -ns 250 -vr 5.0 -vc DC -sr 50000000 \
                -ref 50.0 -ch "0" -ii 1000000 -pa 10.0
 
iii. To simulate without hardware:
        python niscope_continuously_update_graph.py -op \
            "Simulate=1, DriverSetup=Model:5162; BoardType:PXIe"
"""

# Module imports
import argparse                            # For parsing command-line arguments
import sys                                 # For accessing command-line arguments

import matplotlib.pyplot as plt            # For plotting waveforms
import matplotlib.ticker as ticker         # For formatting axis tick labels 
import matplotlib.animation as animation   # For creating animated plots

import niscope                             # For NI Scope Instruments


def example(resource_name, options, num_samples, vertical_range,
             vertical_coupling, sample_rate, ref_position,
             channels, input_impedance, probe_attenuation):
    """
    Core measurement logic - Creates an oscilloscope session, configures
    immediate trigger mode, acquires waveform data, and displays results in an
    animated plot for real-time visualization.

    Args:
        resource_name (str): Resource name of the Scope (e.g., 'PXIe5162')
        options (dict): Driver options for the Scope session (e.g., {'Simulate': '1', 'DriverSetup': 'Model:5162; BoardType:PXIe'})
        num_samples (int, optional): Number of samples to read. Defaults to 250.0
        vertical_range (float, optional): Voltage range in volts. Defaults to 5.0
        vertical_coupling (str, optional): Coupling mode - 'AC', 'DC', or 'GND'. Defaults to 'DC'
        sample_rate (int, optional): Minimum sample rate in Hz. Defaults to 50000000
        ref_position (float, optional): Reference position as percentage. Defaults to 50.0
        channels (str, optional): Channels to read (comma-separated, e.g., '1,2,3'). Defaults to '0'
        input_impedance (int, optional): Input impedance in ohms (50 or 1000000). Defaults to 1000000
        probe_attenuation (float, optional): Probe scale factor (1, 10, 100, etc.). Defaults to 10.0
    """

    plt.rcParams["figure.figsize"] = [7.50, 3.50] #   Set default figure size for plots
    plt.rcParams["figure.autolayout"] = True #   Enable automatic layout adjustment for plots

    def update_samples(waveforms):
        """Extract waveform samples from the waveform object.
        Args:
            waveforms (list): List of WaveformInfo objects from niscope.read()    
        Returns:
            list: Extracted sample values from the first waveform
        """
        samples = []
        # The 'samples' attribute returns a memory address. To get the samples list, 
        # iterate over waveforms[0].samples and append them to a new list
        for sample in waveforms[0].samples:
            samples.append(sample)
        return samples
    
    # Creation of plot figure and axis
    fig, ax = plt.subplots()

    # 'with' block ensures session.abort() + session.close() are called automatically on exit.
    with niscope.Session(resource_name=resource_name, options=options) as session:
        # Setup: Scope configuration
        coupling_enum = getattr(niscope.VerticalCoupling, vertical_coupling.upper())
        session.configure_vertical(range=vertical_range, coupling=coupling_enum)
        session.configure_horizontal_timing(min_sample_rate=sample_rate, min_num_pts=num_samples, 
                                            ref_position=ref_position, num_records=1, enforce_realtime=True)
        
        # Configure input impedance
        session.input_impedance = input_impedance
        
        # Configure probe attenuation
        session.probe_attenuation = probe_attenuation
        
        # Configure trigger
        session.trigger_type = niscope.TriggerType.IMMEDIATE # Set trigger type to immediate for continuous acquisition
        session.trigger_level = 0.0 # Set trigger level to 0 volts
        session.trigger_slope = niscope.TriggerSlope.POSITIVE # Set trigger slope to positive and positive is rising edge
        session.trigger_delay_time = 0.0 # Set trigger delay time to 0 seconds
        channel_list = [ch.strip() for ch in channels.split(',')] # Create a list of channels from the comma-separated string input
        
        # Initiate: Read and store waveform from first channel to initialize the plot 
        waveforms = session.channels[channel_list[0]].read(num_samples=num_samples) # Read waveform data from the first channel
        
        # Calculate time axis
        x_time = [waveforms[0].x_increment * x for x in range(num_samples)]
        
        # Create line object for plot animation
        line, = ax.plot(x_time, update_samples(waveforms=waveforms))
        
        # Plot configuration
        ax.xaxis.set_major_formatter(ticker.EngFormatter(unit="s")) # Format x-axis tick labels in engineering notation with seconds as the unit
        ax.yaxis.set_major_formatter(ticker.EngFormatter(unit="V")) # Format y-axis tick labels in engineering notation with volts as the unit
        ax.set_xlabel('Time (s)') # Set x-axis label to "Time (s)"
        ax.set_ylabel('Voltage (V)') # Set y-axis label to "Voltage (V)"
        ax.grid() # Enable grid lines on the plot for better readability
        
        def animate(i):
            # Function which constantly reads waveform samples and updates the plot
            waveforms = session.channels[channel_list[0]].read(num_samples=num_samples) # Read waveform data from the first channel
            line.set_ydata(update_samples(waveforms=waveforms)) # Update the y-data of the line object with new waveform samples
            return line, # Return the updated line object for the animation to render
        
        # Animation object to iterate over animate() and constantly update the plot
        ani = animation.FuncAnimation(fig, animate, interval=100, blit=True, save_count=50) 
        
        plt.title(label="Waveform Graph") # Set the title of the plot to "Waveform Graph"
       
        plt.show()      # Display the plot window and start the animation loop
        
        plt.close(fig)  # Close the figure after the plot window is closed to free up resources


def _main(argv):
    """Parses command-line arguments and runs the example."""
    parser = argparse.ArgumentParser(description='NI-SCOPE Continuously Update Graph Example')

    parser.add_argument('-n', '--resource_name', default='PXIe5162', help='Resource name of the NI oscilloscope (default: PXIe5162)')
    parser.add_argument('-op', '--option-string', default='', type=str, help='Driver option string, eg: "Simulate=1, DriverSetup=Model:5162; BoardType:PXIe"')
    parser.add_argument('-ns', '--num-samples', type=int, default=250, help='Number of samples to read (default: 250)')
    parser.add_argument('-vr', '--vertical-range', type=float, default=5.0, help='Vertical range in volts (default: 5.0)')
    parser.add_argument('-vc', '--vertical-coupling', choices=['AC', 'DC', 'GND'], default='DC', help='Vertical coupling mode (default: DC)')
    parser.add_argument('-sr', '--sample-rate', type=int, default=50000000, help='Minimum sample rate in Hz (default: 50000000)')
    parser.add_argument('-ref', '--ref-position', type=float, default=50.0, help='Reference position as percentage (default: 50.0)')
    parser.add_argument('-ch', '--channels', default='0', help='Channels to read (comma-separated, e.g., \'1,2,3\') (default: 0)')
    parser.add_argument('-ii', '--input-impedance', type=int, choices=[50, 1000000], default=1000000, help='Input impedance in ohms: 50 or 1000000 (default: 1000000)')
    parser.add_argument('-pa', '--probe-attenuation', type=float, default=10.0, help='Probe scale factor (1, 10, 100, etc.) (default: 10.0)')
    
    args = parser.parse_args(argv) # Second pass: parse all arguments including custom parameters
    
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
    options = {'Simulate': '1','DriverSetup': 'Model:5162; BoardType:PXIe'}
    example('PXIe5162', options, 250, 5.0, 'DC', 50000000, 50.0, '0', 1000000, 10.0)


def test_main():
    """Simulated CLI test — runs _main() with simulate option string."""
    cmd_line = ['-op', 'Simulate=1, DriverSetup=Model:5162; BoardType:PXIe']
    _main(cmd_line)


# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------
if __name__ == '__main__':
    main()