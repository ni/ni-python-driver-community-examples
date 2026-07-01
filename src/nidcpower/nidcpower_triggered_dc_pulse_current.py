#!/usr/bin/env python3
"""NI-DCPower Triggered DC Pulse Current with Measure Record.

This example uses an SMU which waits for a trigger from a DAQ card's counter
output (at 10 Hz),controlled by the DAQ card's Test Panel in NI-MAX.
This is most important step prior to run this example, as the DAQ card's
counter output must be properly configured to generate the expected trigger signal.

Note : Higher counter frequency might cause the buffer to overflow after
some time passes.Removing the plotting of matplotlib will help in avoiding this.

The example uses the default resource names and pulse parameters.
Modify these values as needed for your measurement setup.

HOW TO RUN:
-----------
i.   From terminal (with default values):
        python nidcpower_triggered_dc_pulse_current.py

ii.  From terminal (with custom values):
        python nidcpower_triggered_dc_pulse_current.py \
            -n "PXI1Slot1" -ch "0" -dn "PXI1Slot2" \
            -ple 20e-3 -sd 0.0 -pnt 200e-6 -pft 50e-6 -sr 1.8e6

iii. To simulate without hardware:
        PowerShell:  python nidcpower_triggered_dc_pulse_current.py \
            -op 'Simulate=1, DriverSetup=Model:4139; BoardType:PXIe'
        cmd.exe:     python nidcpower_triggered_dc_pulse_current.py \
            -op "Simulate=1, DriverSetup=Model:4139; BoardType:PXIe"

"""

# Module imports
import argparse                            # For parsing command-line arguments
import sys                                 # For accessing command-line arguments via sys.argv
from math import floor                     # For floor division in record length calculation

# from matplotlib import animation         # For animated live plot (uncomment only if you want to see the live plot)
from matplotlib import pyplot as plt       # For plotting voltage/current vs time
from matplotlib import ticker              # For axis label formatting

import nidcpower                           # NI-DCPower instrument driver


def example(
    smu_resource_name, smu_channel, daq_resource_name, options, pulse_level, source_delay, pulse_on_time,
    pulse_off_time, sample_rate, pulse_voltage_limit, pulse_bias_voltage_limit):
    """
    Perform triggered DC pulse current sourcing and measurement using NI-DCPower,
    triggered by a DAQ card counter output via PXI trigger line.

    Args:
        smu_resource_name (str):
            NI-DCPower SMU device identifier (eg: "PXI1Slot1")

        smu_channel (str):
            Channel number for the SMU (eg: "0")

        daq_resource_name (str):
            NI-DAQ device identifier used as trigger source (eg: "PXI1Slot2")

        options (str or dict):
            Driver options, eg: "" for real HW or simulate string for simulation

        pulse_level (float):
            Pulse current level (A)
            eg: 20e-3 → 20 mA

        source_delay (float):
            Source delay (s)
            eg: 0.0 → no delay

        pulse_on_time (float):
            Pulse on time (s)
            eg: 200e-6 → 200 µs

        pulse_off_time (float):
            Pulse off time (s)
            eg: 50e-6 → 50 µs

        sample_rate (float):
            Target sample rate (S/s)
            eg: 1.8e6 → 1.8 MS/s

        pulse_voltage_limit (float):
            Voltage limit for pulse mode (V)
            eg: 2.0 → 2 V

        pulse_bias_voltage_limit (float):
            Bias voltage limit for pulse mode (V)
            eg: 2.0 → 2 V

    Returns:
        None — results are printed to console and displayed as an animated voltage/current vs time graph
    """

    # -> Set Up Graph
    # - Configures figure size and creates dual subplots (voltage + current)
    voltage_points = [] # List to hold voltage measurements for plotting
    current_points = [] # List to hold current measurements for plotting
    time_points = [] # List to hold time points for plotting

    plt.rcParams["figure.figsize"] = [7.50, 3.50]
    plt.rcParams["figure.autolayout"] = True
    fig, (ax0, ax1) = plt.subplots(nrows=2, figsize=(7, 9.6))

    # -> Initialize DCPower Session
    # - Opens communication with the instrument
    # - 'with' ensures automatic cleanup of session resources
    with nidcpower.Session(resource_name=smu_resource_name, channels=smu_channel, options=options) as session:

        # -> Configure Source Mode and Output Function
        # - source_mode     → SEQUENCE
        # - output_function → PULSE_CURRENT
        # - Load pulse current sequence
        session.source_mode = nidcpower.SourceMode.SEQUENCE
        session.output_function = nidcpower.OutputFunction.PULSE_CURRENT
        session.set_sequence(values=[pulse_level], source_delays=[source_delay])

        # -> Configure Pulse Settings
        # - Set current range, bias level, voltage limits, timing, and transient response
        session.pulse_current_level_range = abs(session.pulse_current_level)
        session.pulse_bias_current_level = 0.0
        session.pulse_voltage_limit = pulse_voltage_limit
        session.pulse_voltage_limit_range = abs(session.pulse_voltage_limit)
        session.pulse_bias_voltage_limit = pulse_bias_voltage_limit
        session.pulse_on_time = pulse_on_time
        session.pulse_off_time = pulse_off_time
        session.pulse_bias_delay = 0.0

        # -> Configure Measurement Settings
        # - Set source delay, transient response, and aperture time
        session.source_delay = source_delay
        session.transient_response = nidcpower.TransientResponse.FAST
        session.aperture_time = 1 / sample_rate

        # - Set initial record length, then recalculate from actual sample rate
        # - Infinite sequence loop with large buffer
        session.measure_record_length = 2
        session.measure_when = nidcpower.MeasureWhen.ON_MEASURE_TRIGGER

        actual_sample_rate = 1 / session.aperture_time # Calculate actual sample rate based on aperture time

        session.measure_record_length = int(floor(actual_sample_rate * (pulse_on_time + pulse_off_time)))
        session.sequence_loop_count_is_finite = False
        session.measure_buffer_size = int(20e6)

        # -> Configure Trigger Settings
        # - Start and sequence advance triggers from DAQ PFI12 channel (counter output)
        # - Measure trigger from SMU's own SourceCompleteEvent
        session.start_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE
        session.digital_edge_start_trigger_input_terminal = f"/{daq_resource_name}/PFI12"
        session.sequence_advance_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE
        session.digital_edge_sequence_advance_trigger_input_terminal = f"/{daq_resource_name}/PFI12"
        session.measure_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE

        # This will automatically use the resource_name specified at the beginning of the NI-DCPower session.
        session.digital_edge_measure_trigger_input_terminal = f"/{smu_resource_name}/Engine{smu_channel}/SourceCompleteEvent"

        # -> Initiate and Fetch Initial Measurements
        # - Starts pulse generation
        # - Fetches first record and prints timing info
        session.initiate()

        samples_acquired = 0 # Initialize counter for total samples acquired
    
        measurements = session.channels[0].fetch_multiple(count=session.measure_record_length)
        samples_acquired += len(measurements)

        aperture_time = "{:.2e}".format(session.aperture_time)      # Formats aperture time for more readability.
        sample_rate = "{:.2e}".format(1 / session.aperture_time)    # Formats sample rate for more readability.

        # Prints Aperture time, Actual Sample Rate and size of measurement to console for user reference.
        print(f"\nAperture Time: {aperture_time} seconds\nActual Sample Rate: {sample_rate} S/s")
        print("Size: ", len(measurements))

        # Prepare voltage and current points for plotting.
        for measure in measurements:
            voltage_points.append(measure[0])
            current_points.append(measure[1])

        # Prints the number of measurements that are still in the buffer and have not been fetched yet.
        print("Fetch Backlog: ", session.fetch_backlog) 

        # Prepare time points for plotting based on the aperture time and the number of measurements.
        time_points = [session.aperture_time * x for x in range(session.measure_record_length)]

        # -> Configure Graph Axes     
        # ax0 corresponds to the voltage graph.
        ax0.xaxis.set_major_formatter(ticker.EngFormatter(unit="s"))
        ax0.yaxis.set_major_formatter(ticker.EngFormatter(unit="V"))
        ax0.set_xlim(0, session.aperture_time*len(measurements))
        ax0.set_xlabel('Time (s)')
        ax0.set_ylabel('Voltage (V)')
        ax0.grid()
        volt_line, = ax0.plot(time_points, voltage_points)

        # ax1 corresponds to the current graph.
        ax1.xaxis.set_major_formatter(ticker.EngFormatter(unit="s"))
        ax1.yaxis.set_major_formatter(ticker.EngFormatter(unit="A"))
        ax1.set_xlim(0, session.aperture_time*len(measurements))
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Current (A)')
        ax1.grid()
        current_line, = ax1.plot(time_points, current_points)

        # -> Configure and Display Animated Graph (uncomment the following block to enable live plotting)
        # - Sets up voltage and current plot lines
        # - Defines animation function to continuously update plots
           
        """
        def animate(i):
            # Animate and update plot constantly
            voltage_points = []
            current_points = []
            measurements = session.channels[0].fetch_multiple(count=session.measure_record_length)
            for measure in measurements:
                voltage_points.append(measure[0])
                current_points.append(measure[1])

            volt_line.set_data(time_points, voltage_points)
            current_line.set_data(time_points, current_points)

            return volt_line, current_line


        # FuncAnimation class which repeatedly calls the animate function to constantly update plot.
          ani = animation.FuncAnimation(fig, animate, interval=50, repeat=False, blit=True, cache_frame_data=False)

        """

        fig.canvas.manager.set_window_title(
            "NI-DCPower triggered dc pulse current"
        ) # Sets the window title for the graph display

        plt.show() # Display the animated plot

        plt.close(fig) # Close the figure to free up memory after the plot window is closed


def _main(argsv):
    """Parses command-line arguments and calls example() with the parsed values."""
    parser = argparse.ArgumentParser(
        description='Triggered DC pulse current: pulse current with measure record and live plot.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-n',   '--smu-resource-name',        default='PXI1Slot1', help='SMU resource name')
    parser.add_argument('-ch',  '--smu-channel',              default='0',         help='SMU channel')
    parser.add_argument('-dn',  '--daq-resource-name',        default='PXI1Slot2', help='DAQ resource name (trigger source)')
    parser.add_argument('-ple',  '--pulse-level',             default=20e-3,  type=float, help='Pulse current level (A)')
    parser.add_argument('-sd',  '--source-delay',             default=0.0,    type=float, help='Source delay (s)')
    parser.add_argument('-pnt', '--pulse-on-time',            default=200e-6, type=float, help='Pulse on time (s)')
    parser.add_argument('-pft', '--pulse-off-time',           default=50e-6,  type=float, help='Pulse off time (s)')
    parser.add_argument('-sr',  '--sample-rate',              default=1.8e6,  type=float, help='Target sample rate (S/s)')
    parser.add_argument('-pvl', '--pulse-voltage-limit',      default=2.0,    type=float, help='Voltage limit for pulse mode (V)')
    parser.add_argument('-pbvl', '--pulse-bias-voltage-limit',default=2.0,   type=float, help='Bias voltage limit for pulse mode (V)')
    parser.add_argument('-op',  '--option-string',            default='',     type=str,   help='Driver option string, eg: "Simulate=1, DriverSetup=Model:4139; BoardType:PXIe"')
    args = parser.parse_args(argsv)
    example(
        smu_resource_name=args.smu_resource_name,
        smu_channel=args.smu_channel,
        daq_resource_name=args.daq_resource_name,
        options=args.option_string,
        pulse_level=args.pulse_level,
        source_delay=args.source_delay,
        pulse_on_time=args.pulse_on_time,
        pulse_off_time=args.pulse_off_time,
        sample_rate=args.sample_rate,
        pulse_voltage_limit=args.pulse_voltage_limit,
        pulse_bias_voltage_limit=args.pulse_bias_voltage_limit,
    )


def main():
    """Entry point — passes real CLI args to _main()."""
    _main(sys.argv[1:])


def test_example():
    """Simulated hardware test — runs example() with a virtual PXIe-4139 (no real HW needed)."""
    options = {'simulate': True, 'driver_setup': {'Model': '4139', 'BoardType': 'PXIe'}}
    example(
        smu_resource_name='PXI1Slot1',
        smu_channel='0',
        daq_resource_name='PXI1Slot2',
        options=options,
        pulse_level=20e-3,
        source_delay=0.0,
        pulse_on_time=200e-6,
        pulse_off_time=50e-6,
        sample_rate=1.8e6,
        pulse_voltage_limit=2.0,
        pulse_bias_voltage_limit=2.0,
    )
    plt.close('all') # Close all figures


def test_main():
    """Simulated CLI test — runs _main() with simulate option string."""
    plt.switch_backend('Agg') # Switch to non-interactive backend for testing
    cmd_line = [
        '--option-string',
        'Simulate=1, DriverSetup=Model:4139; BoardType:PXIe',
    ]
    _main(cmd_line)
    plt.close('all')


# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------
if __name__ == '__main__':
    main()
