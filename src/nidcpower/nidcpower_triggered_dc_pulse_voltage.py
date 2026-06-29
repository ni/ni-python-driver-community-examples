#!/usr/bin/env python3
"""NI-DCPower Triggered DC Pulse Voltage Example.

This example demonstrates how to generate triggered voltage pulses using an NI-DCPower SMU
and acquire high-speed voltage and current measurements using Measure Record.

The SMU waits for a digital trigger from a DAQ device. Each trigger initiates a pulse sequence,
and measurements are captured using the SourceCompleteEvent as the measurement trigger source.

HOW TO RUN:
-----------
i. From terminal (with default values):
    python nidcpower_triggered_dc_pulse_voltage.py --

ii. From terminal (with custom values):
    python nidcpower_triggered_dc_pulse_voltage.py \
        -n "PXI1Slot1" -d "PXI1Slot2" -pvl 2.0 -pnt 100e-6 -pft 100e-6 -sr \
            1.8e6 -mbs 20000000 -pclt 1e-1  -pbclt 1e-1 -pvbl 0.0 -sd 0 --op ""

iii. To simulate without hardware:
    python nidcpower_triggered_dc_pulse_voltage.py \
        -op "Simulate=1,DriverSetup=Model:4139;BoardType:PXIe"
"""

# Module imports
import argparse                  # argparse is used to parse command line arguments
import sys                       # sys is used to access command line arguments
from math import floor

import matplotlib.pyplot as plt  # for plotting the voltage and current waveforms
from matplotlib import ticker    # for formatting the axes of the plots

import nidcpower                 # for DCPower Instrument control


def example(resource_name, daq_resource_name, pulse_level, pulse_on_time, pulse_off_time, sample_rate, measure_buffer_size,
            pulse_current_limit, pulse_bias_current_limit, pulse_bias_voltage_level, source_delay, options):
    """
    Core measurement logic — opens session, configures pulse generation,
    acquires measure-record data, and returns waveform arrays.

    Args:
        resource_name (str): NI-DCPower resource name.
        daq_resource_name (str): DAQ device used to provide digital trigger signals.
        pulse_level (float): Pulse voltage level in volts.
        pulse_on_time (float): Pulse on-time in seconds.
        pulse_off_time (float): Pulse off-time in seconds.
        sample_rate (float): Sample rate in Hz.
        measure_buffer_size (int): Measurement buffer size.
        pulse_current_limit (float): Pulse current limit in amperes.
        pulse_bias_current_limit (float): Pulse bias current limit in amperes.
        pulse_bias_voltage_level (float): Pulse bias voltage level in volts.
        source_delay (float): Source delay in seconds.
        options (str): Driver initialization options.

    """
    voltage_points = [] # List to store voltage measurements
    current_points = [] # List to store current measurements

    plt.rcParams["figure.figsize"] = [7.50, 3.50] # Set the default figure size for plots
    plt.rcParams["figure.autolayout"] = True # Enable automatic layout adjustment for plots

    fig, (ax0, ax1) = plt.subplots(nrows=2, figsize=(7, 9.6)) # Create a figure with two subplots (ax0 for voltage, ax1 for current)

    # 'with' ensures automatic cleanup of session resources
    with nidcpower.Session(resource_name=resource_name, options=options) as session:

        session.source_mode = nidcpower.SourceMode.SEQUENCE # Set the source mode to SEQUENCE
        session.output_function = nidcpower.OutputFunction.PULSE_VOLTAGE # Set the output function to PULSE_VOLTAGE
        session.set_sequence(values=[pulse_level],source_delays=[source_delay]) # Set the sequence values and source delays
        session.pulse_voltage_level_range = abs(session.pulse_voltage_level) # Set the pulse voltage level range to the absolute value of the pulse voltage level
        session.pulse_bias_voltage_level = pulse_bias_voltage_level # Set the pulse bias voltage level
        session.pulse_current_limit = pulse_current_limit # Set the pulse current limit
        session.pulse_current_limit_range = abs(session.pulse_current_limit) # Set the pulse current limit range to the absolute value of the pulse current limit
        session.pulse_bias_current_limit = pulse_bias_current_limit # Set the pulse bias current limit
        session.pulse_on_time = pulse_on_time 
        session.pulse_off_time = pulse_off_time
        session.pulse_bias_delay = 0
        session.source_delay = source_delay # Set the source delay

        session.transient_response = (nidcpower.TransientResponse.NORMAL) # Set the transient response to NORMAL

        session.aperture_time = 1 / sample_rate # Set the aperture time to the inverse of the sample rate
        actual_sample_rate = (1 / session.aperture_time) # Set the actual sample rate to the inverse of the aperture time
        session.measure_when = (nidcpower.MeasureWhen.ON_MEASURE_TRIGGER) # Set the measure when to ON_MEASURE_TRIGGER
        session.measure_record_length = int(floor(actual_sample_rate *(pulse_on_time +pulse_off_time +10e-6)))
        session.sequence_loop_count_is_finite = False
        session.measure_buffer_size = int(measure_buffer_size)

        # Trigger Configuration
        session.start_trigger_type = (nidcpower.TriggerType.DIGITAL_EDGE)
        session.digital_edge_start_trigger_input_terminal = (f"/{daq_resource_name}/PFI12") # Set the start trigger input terminal to the PFI12 of the DAQ device
        session.sequence_advance_trigger_type = (nidcpower.TriggerType.DIGITAL_EDGE) # Set the sequence advance trigger type to DIGITAL_EDGE
        session.digital_edge_sequence_advance_trigger_input_terminal = (f"/{daq_resource_name}/PFI12") # Set the sequence advance trigger input terminal to the PFI12 of the DAQ device
        session.measure_trigger_type = (nidcpower.TriggerType.DIGITAL_EDGE) # Set the measure trigger type to DIGITAL_EDGE
        session.digital_edge_measure_trigger_input_terminal = (f"/{resource_name}/Engine0/SourceCompleteEvent")

        # Commit to send all settings to hardware before initiate.
        session.commit()

        # Opens communication with the instrument
        session.initiate()

        # Measurement
        measurements = session.channels[0].fetch_multiple(count=session.measure_record_length)

        # print the number of measurements acquired, aperture time, actual sample rate, and fetch backlog
        print(f"Measurements Acquired: {len(measurements)}")
        print(f"Aperture Time: {session.aperture_time:.2e} seconds")
        print(f"Actual Sample Rate: {1 / session.aperture_time:.2e} S/s")
        print(f"Fetch Backlog: {session.fetch_backlog}")

        # Prepare voltage and current points for plotting.
        for measure in measurements:
            voltage_points.append(measure[0])
            current_points.append(measure[1])

        # Prepare time points for plotting based on the aperture time and the number of measurements. 
        time_points = [session.aperture_time * x for x in range(session.measure_record_length)]

        # ax0 corresponds to the voltage graph.
        ax0.xaxis.set_major_formatter(ticker.EngFormatter(unit="s"))
        ax0.yaxis.set_major_formatter(ticker.EngFormatter(unit="V"))
        ax0.set_xlim(0, session.aperture_time*len(measurements))
        ax0.set_xlabel('Time (s)')
        ax0.set_ylabel('Voltage (V)')
        ax0.grid()
        ax0.plot(time_points, voltage_points)

        # ax1 corresponds to the current graph.
        ax1.xaxis.set_major_formatter(ticker.EngFormatter(unit="s"))
        ax1.yaxis.set_major_formatter(ticker.EngFormatter(unit="A"))
        ax1.set_xlim(0, session.aperture_time*len(measurements))
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Current (A)')
        ax1.grid()
        ax1.plot(time_points, current_points)

        fig.suptitle("NI-DCPower Triggered DC Pulse Voltage") # Set the title for the entire figure

        plt.show()      # Display the plot with the voltage and current waveforms

        plt.close(fig)  # Close the figure to free up memory and resources


def _main(argsv):
    """Command line interface — parses arguments and calls example()."""
    parser = argparse.ArgumentParser(description="NI-DCPower Triggered Pulse Measure Record Example")

    parser.add_argument("-n",       "--resource-name",                         default="PXI1Slot1",    help="NI-DCPower resource name")
    parser.add_argument("-d",       "--daq-resource-name",                     default="PXI1Slot2",    help="DAQ resource used for trigger generation")
    parser.add_argument("-pvl",     "--pulse-voltage-level",       type=float, default=2.0,            help="Pulse voltage level")
    parser.add_argument("-pnt",     "--pulse-on-time",             type=float, default=100e-6,         help="Pulse on-time in seconds")
    parser.add_argument("-pft",     "--pulse-off-time",            type=float, default=100e-6,         help="Pulse off-time in seconds")
    parser.add_argument("-sr",      "--sample-rate",               type=float, default=1.8e6,          help="Sample rate in Hz")
    parser.add_argument("-mbs",     "--measure-buffer-size",       type=int,   default=int(20e6),      help="Measurement buffer size")
    parser.add_argument("-pclt",    "--pulse-current-limit",       type=float, default=1e-1,           help="Pulse current limit in amperes")
    parser.add_argument("-pbclt",   "--pulse-bias-current-limit",  type=float, default=1e-1,           help="Pulse bias current limit in amperes")
    parser.add_argument("-pvbl",    "--pulse-bias-voltage-level",  type=float, default=0.0,            help="Pulse bias voltage level in volts")
    parser.add_argument("-sd",      "--source-delay",              type=float, default=0,              help="Source delay in seconds")
    parser.add_argument("-op",      "--options",                               default="",             help="Driver initialization options")

    args = parser.parse_args(argsv)

    example(
        resource_name=args.resource_name,
        daq_resource_name=args.daq_resource_name,
        pulse_voltage_level=args.pulse_voltage_level,
        pulse_on_time=args.pulse_on_time,
        pulse_off_time=args.pulse_off_time,
        sample_rate=args.sample_rate,
        measure_buffer_size=args.measure_buffer_size,
        pulse_current_limit=args.pulse_current_limit,
        pulse_bias_current_limit=args.pulse_bias_current_limit,
        pulse_bias_voltage_level=args.pulse_bias_voltage_level,
        source_delay=args.source_delay,
        options=args.options)


def main():
    """Entry point — passes real CLI args to _main()."""
    _main(sys.argv[1:])


def test_example():
    """Simulated hardware test — runs example() with a simulated PXIe-4139 (no real HW needed)."""
    options = "Simulate=1,DriverSetup=Model:4139;BoardType:PXIe"
    example("PXI1Slot1", "PXI1Slot2", 2.0, 100e-6, 100e-6, 1.8e6, int(20e6), 1e-1, 1e-1, 0.0, 0, options)


def test_main():
    """Simulated CLI test — runs _main() with simulate option string."""
    cmd_line = ["-op", "Simulate=1,DriverSetup=Model:4139;BoardType:PXIe"]
    _main(cmd_line)


# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------
if __name__ == '__main__':
    main()
