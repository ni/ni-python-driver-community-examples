#!/usr/bin/env python3
""" NI-DCPower Sequence Mode - Transient Response Plot

This example demonstrates how to capture and plot the transient response of an NI SMU 
while operating in Sequence Source Mode.

Configures an NI-DCPower session for voltage sequencing, sets transient response parameters, 
measures voltage/current continuously during execution, and plots the captured transient response.

HOW TO RUN:
-----------
i.   From terminal (with default values):
        python nidcpower_sequence_mode_transient_response.py

ii.  From terminal (with custom values):
    python nidcpower_sequence_mode_transient_response.py  \
        -n "NISMU"  -sv [0.0, 1.0, 2.0] sd [0.0001, 0.0001, 0.0001]  -vr 6.0  \
            -m 250 -at 0.0001 -tr NORMAL    
    python nidcpower_sequence_mode_transient_response.py  \
        -n "NISMU"  -sv [0.0, 1.0, 2.0] sd [0.0001, 0.0001, 0.0001]  -vr 6.0  \
            -m 250 -at 0.0001 -tr CUSTOM -vgb 5000 -vcf 50000 -vpzr 0.16 \
                -cgb 40000 -ccf 250000 -cpzr 4

iii. To simulate without hardware:
        python nidcpower_sequence_mode_transient_response.py \
            -op "Simulate=1, DriverSetup=Model:4139; BoardType:PXIe"
"""

# Module imports
import argparse                  # argparse is used to parse command line arguments
import sys                       # sys is used to access command line arguments

import matplotlib.pyplot as plt  # for plotting the voltage and current waveforms
from matplotlib import ticker    # for formatting the axes of the plots

import nidcpower                 # For DCPower instrument control


def example(resource_name,options,sequence_voltages,source_delays,voltage_range,
            measure_record_length,aperture_time,transient_response,
            voltage_gain_bandwidth,voltage_compensation_frequency,
            voltage_pole_zero_ratio,current_gain_bandwidth,
            current_compensation_frequency,current_pole_zero_ratio):
    """
    Core measurement logic — opens session, configures sequence mode and transient response parameters, 
    sources voltage, measures current, and plots results.

    Args:
        resource_name (str): NI-DCPower resource name.
        options (str): Driver option string.
        sequence_voltages (list[float]): Voltage levels for the sequence.
        source_delays (list[float]): Per-step source delays in seconds.
        voltage_range (float): Voltage range in volts.
        measure_record_length (int): Number of samples to acquire per record.
        aperture_time (float): Measurement integration time in seconds (0 = driver default).
        transient_response (str): SLOW, NORMAL, FAST or CUSTOM.
        voltage_gain_bandwidth (float): Voltage gain bandwidth (CUSTOM mode only).
        voltage_compensation_frequency (float): Voltage compensation frequency (CUSTOM mode only).
        voltage_pole_zero_ratio (float): Voltage pole-zero ratio (CUSTOM mode only).
        current_gain_bandwidth (float): Current gain bandwidth (CUSTOM mode only).
        current_compensation_frequency (float): Current compensation frequency (CUSTOM mode only).
        current_pole_zero_ratio (float): Current pole-zero ratio (CUSTOM mode only).
    """

    voltage_points = [] # List to store voltage measurements
    current_points = [] # List to store current measurements

    plt.rcParams["figure.figsize"] = [7.50, 3.50] # Set default figure size for plots
    plt.rcParams["figure.autolayout"] = True # Enable automatic layout adjustment for plots

    fig, (ax0, ax1) = plt.subplots(nrows=2, figsize=(7, 9.6)) # Create a figure with two subplots (one for voltage, one for current)

    # 'with' ensures automatic cleanup of session resources
    with nidcpower.Session(resource_name=resource_name, options=options) as session:

        session.source_mode = nidcpower.SourceMode.SEQUENCE # Set source mode to SEQUENCE
        session.output_function = nidcpower.OutputFunction.DC_VOLTAGE # Set output function to DC voltage
        session.voltage_level_range = voltage_range # Set voltage range
        session.set_sequence(sequence_voltages,source_delays) # Set sequence voltages and source delays
        session.aperture_time_units = nidcpower.ApertureTimeUnits.SECONDS # set the aperture time units to seconds
        session.aperture_time = aperture_time # set the aperture time
        
        session.transient_response = transient_response # Set the transient response mode (SLOW, NORMAL, FAST, CUSTOM)

        # Only set custom transient parameters if transient_response is CUSTOM
        if transient_response == nidcpower.TransientResponse.CUSTOM:
            session.voltage_gain_bandwidth = voltage_gain_bandwidth
            session.voltage_compensation_frequency = voltage_compensation_frequency
            session.voltage_pole_zero_ratio = voltage_pole_zero_ratio
            session.current_gain_bandwidth = current_gain_bandwidth
            session.current_compensation_frequency = current_compensation_frequency
            session.current_pole_zero_ratio = current_pole_zero_ratio

        session.measure_when = nidcpower.MeasureWhen.ON_MEASURE_TRIGGER # Set measure when to ON_MEASURE_TRIGGER
        session.exported_start_trigger_output_terminal = f"/{resource_name}/PXI_Trig0" # Export the start trigger to PXI_Trig0
        session.measure_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE # Set measure trigger type to DIGITAL_EDGE
        session.digital_edge_measure_trigger_input_terminal = f"/{resource_name}/PXI_Trig0" # Set digital edge measure trigger input terminal
        session.measure_record_length = measure_record_length  # Set the number of samples to acquire per record
        session.measure_record_length_is_finite = False  # Set the measure record length to be infinite (continuous acquisition)

        session.output_enabled = True  # Enable the output
        
        # Commit sends all settings to hardware before initiate.
        session.commit()

        # Opens communication with the instrument
        session.initiate()

        measurements = session.channels[0].fetch_multiple(count=session.measure_record_length) # Fetch multiple measurements from the first channel

        print(f"Measurements Acquired: {len(measurements)}")  #Print the number of measurements acquired
        print(f"Aperture Time: {session.aperture_time:.2e} seconds")  #Print the aperture time in seconds

        if session.aperture_time > 0: #Print the sample rate in samples per second if aperture time is greater than 0
            print(f"Sample Rate: {1 / session.aperture_time:.2e} S/s") #Print the sample rate in samples per second

        # Print transient settings only if CUSTOM mode
        if transient_response == nidcpower.TransientResponse.CUSTOM:
            transient_settings = {
                "Voltage Gain Bandwidth": session.voltage_gain_bandwidth,
                "Voltage Compensation Frequency": session.voltage_compensation_frequency,
                "Voltage Pole Zero Ratio": session.voltage_pole_zero_ratio,
                "Current Gain Bandwidth": session.current_gain_bandwidth,
                "Current Compensation Frequency": session.current_compensation_frequency,
                "Current Pole Zero Ratio": session.current_pole_zero_ratio
            }
            print("\nTransient Response Settings (CUSTOM):")
            print(transient_settings)
        else:
            print(f"\nTransient Response Mode: {transient_response}")

        # Store Data for Plotting
        for measurement in measurements: # Iterate through the measurements and append voltage and current to their respective lists
            voltage_points.append(measurement[0])
            current_points.append(measurement[1])


        # Calculate time points for plotting based on aperture time and number of measurement
        time_points = [session.aperture_time * x for x in range(len(measurements))]

        # Plot Voltage
        ax0.xaxis.set_major_formatter(ticker.EngFormatter(unit="s"))
        ax0.yaxis.set_major_formatter(ticker.EngFormatter(unit="V"))
        ax0.set_xlabel("Time (s)")
        ax0.set_ylabel("Voltage (V)")
        ax0.grid()
        ax0.plot(time_points, voltage_points)

        # Plot Current
        ax1.xaxis.set_major_formatter(ticker.EngFormatter(unit="s"))
        ax1.yaxis.set_major_formatter(ticker.EngFormatter(unit="A"))
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Current (A)")
        ax1.grid()
        ax1.plot(time_points, current_points)

        fig.suptitle("NI-DCPower Sequence Mode Transient Response") # Set the title of the figure

        plt.show() # display the plots eith the voltage and current waveforms

        plt.close(fig) # Close the figure to free up memory


def _main(argsv):
    parser = argparse.ArgumentParser(description="NI-DCPower Sequence Mode Transient Response Plot")

    parser.add_argument('-n', '--resource-name', default='PXI1Slot1', help='Resource name of NI SMU')
    parser.add_argument('-op', '--option-string', default='', type=str, help='Driver option string, eg: "Simulate=1, DriverSetup=Model:4139; BoardType:PXIe"')
    parser.add_argument('-sv', '--sequence-voltages', type=float, nargs='+', default=[0.0, 1.0, 2.0], help='Voltage levels for the sequence (space-separated)')
    parser.add_argument('-sd', '--source-delays', type=float, nargs='+', default=[1e-3, 1e-3, 1e-3], help='Per-step source delays in seconds (space-separated)')
    parser.add_argument('-vr', '--voltage-range', type=float, default=6.0, help='Voltage range (V)')
    parser.add_argument('-m','--measure-record-length', type=int, default=5000, help='Number of samples to acquire per record')
    parser.add_argument('-at',"--aperture-time", type=float, default=0.0001, help='Aperture time in seconds (0 = driver default)')
    parser.add_argument('-tr', '--transient-response', default='CUSTOM', help='Transient response mode (SLOW, FAST, NORMAL, or CUSTOM)')

    # First pass: parse to get transient response mode
    args, remaining_args = parser.parse_known_args(argsv)

    # Add custom transient parameters only if CUSTOM mode is selected
    if args.transient_response.upper() == 'CUSTOM':
        parser.add_argument('-vgb', '--voltage-gain-bandwidth', type=float, default=5000, help='Voltage gain bandwidth (for CUSTOM transient)')
        parser.add_argument('-vcf', '--voltage-compensation-frequency', type=float, default=50000, help='Voltage compensation frequency (for CUSTOM transient)')
        parser.add_argument('-vpzr', '--voltage-pole-zero-ratio', type=float, default=0.16, help='Voltage pole-zero ratio (for CUSTOM transient)')
        parser.add_argument('-cgb', '--current-gain-bandwidth', type=float, default=40000, help='Current gain bandwidth (for CUSTOM transient)')
        parser.add_argument('-ccf', '--current-compensation-frequency', type=float, default=250000, help='Current compensation frequency (for CUSTOM transient)')
        parser.add_argument('-cpzr', '--current-pole-zero-ratio', type=float, default=4, help='Current pole-zero ratio (for CUSTOM transient)')

        # Second pass: parse all arguments including custom parameters
        args = parser.parse_args(argsv)
    else:
        # For non-CUSTOM modes, check if user tried to use custom parameters
        if remaining_args:
            print(f"Warning: Custom transient parameters are only used with --transient-response CUSTOM mode. Ignoring: {remaining_args}")

        # Set default values for custom parameters
        args.voltage_gain_bandwidth = 5000
        args.voltage_compensation_frequency = 50000
        args.voltage_pole_zero_ratio = 0.16
        args.current_gain_bandwidth = 40000
        args.current_compensation_frequency = 250000
        args.current_pole_zero_ratio = 4

    # Convert transient response string to enum
    transient_response_map = {
        'SLOW': nidcpower.TransientResponse.SLOW,
        'FAST': nidcpower.TransientResponse.FAST,
        'NORMAL': nidcpower.TransientResponse.NORMAL,
        'CUSTOM': nidcpower.TransientResponse.CUSTOM,
    }
    transient_response = transient_response_map.get(
        args.transient_response.upper(),
        nidcpower.TransientResponse.NORMAL
    )

    example(
        resource_name=args.resource_name,
        options=args.options,
        sequence_voltages=args.sequence_voltages,
        source_delays=args.source_delays,
        voltage_range=args.voltage_range,
        measure_record_length=args.measure_record_length,
        aperture_time=args.aperture_time,
        transient_response=transient_response,
        voltage_gain_bandwidth=args.voltage_gain_bandwidth,
        voltage_compensation_frequency=args.voltage_compensation_frequency,
        voltage_pole_zero_ratio=args.voltage_pole_zero_ratio,
        current_gain_bandwidth=args.current_gain_bandwidth,
        current_compensation_frequency=args.current_compensation_frequency,
        current_pole_zero_ratio=args.current_pole_zero_ratio)


def main():
    """Entry point — passes real CLI args to _main()."""
    _main(sys.argv[1:])


def test_example():
    """Simulated hardware test — runs example() with a virtual PXIe-4139."""
    options = "Simulate=1, DriverSetup=Model:4139; BoardType:PXIe"
    example("PXI1Slot1",options,[0.0, 1.0, 2.0],[1e-3, 1e-3,1e-3],6.0,5000,0.0001,
            nidcpower.TransientResponse.NORMAL,5000,50000,0.16,40000,250000,4)


def test_main():
    """Simulated CLI test — runs _main() with simulate option string."""
    cmd_line = [  "-n", "NISMU","-op","Simulate=1,DriverSetup=Model:4139;BoardType:PXIe"]
    _main(cmd_line)


# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------
if __name__ == '__main__':
    main()
