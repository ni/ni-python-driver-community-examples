#!/usr/bin/env python3
"""NI-DCPower Single Point - Transient Response Plot

This example demonstrates how to capture and plot the transient response
of an NI-DCPower SMU while operating in Single Point Source Mode.

The example:
    - Configures the SMU for DC voltage sourcing
    - Configures continuous measurements using Measure Trigger
    - Captures voltage and current samples
    - Plots voltage vs time and current vs time
    - Displays transient response characteristics

HOW TO RUN:
-----------
i. From terminal (with default values):
    python nidcpower_single_point_transient_response.py

ii. From terminal (with custom values):
    python nidcpower_single_point_transient_response.py  -n "NISMU"  -v 1.0  -r 6.0  -m 250 \
        -at 0.0001 -sd 0.0001 -tr NORMAL    
    python nidcpower_single_point_transient_response.py  -n "NISMU"  -v 1.0  -r 6.0  -m 250 \
        -at 0.0001 -sd 0.0001 -tr CUSTOM -vgb 5000 -vcf 50000 -vpzr 0.16 -cgb 40000 -ccf 250000 -cpzr 4

iii. To simulate without hardware:
    PowerShell:  python nidcpower_hardware_timed_single_point.py -op 'Simulate=1, DriverSetup=Model:4139; BoardType:PXIe'
    cmd.exe:     python nidcpower_hardware_timed_single_point.py -op "Simulate=1, DriverSetup=Model:4139; BoardType:PXIe"
"""

import argparse # for parsing command line arguments
import sys # for accessing command line arguments
import time # for measuring execution time

import matplotlib.pyplot as plt # for plotting data
import matplotlib.ticker as ticker # for customizing plot tick marks

import nidcpower # for controlling NI-DCPower instruments


def example(resource_name, options, voltage_level, voltage_level_range, measure_record,
             aperture_time, source_delay, transient_response,
             voltage_gain_bandwidth, voltage_compensation_frequency,
             voltage_pole_zero_ratio, current_gain_bandwidth ,
             current_compensation_frequency, current_pole_zero_ratio):
    """
    Core measurement logic — opens session, configures,
    sources, measures, and plots transient response.
    Args:
        resource_name (str): NI-DCPower resource name.
        options (str): Driver option string.
        voltage_level (float): Output voltage level in volts.
        voltage_range (float): Voltage range in volts.
        measure_record (int): Number of samples to acquire.
        aperture_time (float): Measurement integration time in seconds.
        source_delay (float): Delay before measurement in seconds.
        transient_response (str): Transient response mode.
        voltage_gain_bandwidth (float): Voltage gain bandwidth.
        voltage_compensation_frequency (float): Voltage compensation frequency.
        voltage_pole_zero_ratio (float): Voltage pole-zero ratio.
        current_gain_bandwidth (float): Current gain bandwidth.
        current_compensation_frequency (float): Current compensation frequency.
        current_pole_zero_ratio (float): Current pole-zero ratio.
    """
    voltage_points = [] # list to store voltage measurement points for plotting
    current_points = [] # list to store current measurement points for plotting

    plt.rcParams["figure.figsize"] = [7.50, 3.50] # set the figure size
    plt.rcParams["figure.autolayout"] = True #` enable automatic layout for the figure`

    fig, (ax0, ax1) = plt.subplots(nrows=2,figsize=(7, 9.6))

    with nidcpower.Session(resource_name=resource_name, channels=0, reset=True, options=options, independent_channels=True) as session:

        session.source_mode = nidcpower.SourceMode.SINGLE_POINT #source mode is set to single point
        session.output_function = nidcpower.OutputFunction.DC_VOLTAGE #output function is set to DC voltage
        session.voltage_level = voltage_level # set the voltage level to the specified value
        session.voltage_level_range = voltage_level_range # set the voltage range to the specified value
        session.aperture_time_units = nidcpower.ApertureTimeUnits.SECONDS # set the aperture time units to seconds
        session.aperture_time = aperture_time # set the aperture time
        session.source_delay = source_delay # set the source delay

        session.transient_response = transient_response # set the transient response

        # Only set custom transient parameters if transient_response is CUSTOM
        if transient_response == nidcpower.TransientResponse.CUSTOM:
            session.voltage_gain_bandwidth = voltage_gain_bandwidth
            session.voltage_compensation_frequency = voltage_compensation_frequency
            session.voltage_pole_zero_ratio = voltage_pole_zero_ratio
            session.current_gain_bandwidth = current_gain_bandwidth
            session.current_compensation_frequency = current_compensation_frequency
            session.current_pole_zero_ratio = current_pole_zero_ratio

        session.measure_when = nidcpower.MeasureWhen.ON_MEASURE_TRIGGER # set the measure when to on measure trigger
        session.exported_start_trigger_output_terminal =  f"/{resource_name}/PXI_Trig0" # set the exported start trigger output terminal to PXI_Trig0
        session.measure_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE # set the measure trigger type to digital edge
        session.digital_edge_measure_trigger_input_terminal = f"/{resource_name}/PXI_Trig0" # set the digital edge measure trigger input terminal to PXI_Trig0
        session.measure_record_length_is_finite = False # set the measure record length to be infinite
        session.measure_record_length = measure_record # set the measure record length to the specified value
        session.measure_buffer_size = 20000000 # set the measure buffer size to 20 million samples
        session.output_enabled = True # enable the output
        # Commit
        session.commit()
        # - Opens communication with the instrument
        # - 'with' ensures automatic cleanup of session resources
        session.initiate()
        start_time = time.time() # record the start time for performance measurement
        measurements = session.channels[0].fetch_multiple(count=session.measure_record_length)  # fetch the measurements for the specified record length
        end_time = time.time()      # record the end time for performance measurement

        print(f"Generation Time: "f"{end_time - start_time:.6f} seconds") # print the time taken to generate the measurements)
        print(f"Measurements Acquired: {len(measurements)}") # print the number of measurements acquired
        print(f"Aperture Time: " f"{session.aperture_time:.2e} seconds") # print the aperture time
        if session.aperture_time > 0:
            print(f"Sample Rate: " f"{1/session.aperture_time:.2e} S/s") # print the sample rate

        # Print transient settings only if CUSTOM mode
        if transient_response == nidcpower.TransientResponse.CUSTOM:
            transient_settings = {
                "Voltage Gain Bandwidth":session.voltage_gain_bandwidth,
                "Voltage Compensation Frequency":session.voltage_compensation_frequency,
                "Voltage Pole Zero Ratio":session.voltage_pole_zero_ratio,
                "Current Gain Bandwidth":session.current_gain_bandwidth,
                "Current Compensation Frequency":session.current_compensation_frequency,
                "Current Pole Zero Ratio":session.current_pole_zero_ratio
            }

            print("\nTransient Response Settings (CUSTOM):")
            print(transient_settings)
        else:
            print(f"\nTransient Response Mode: {transient_response}")
        # Store Data for Plotting
        for measurement in measurements:
            voltage_points.append(measurement[0])
            current_points.append(measurement[1])

        x_time = [session.aperture_time * x for x in range(len(measurements))]
        # Plot Voltage
        ax0.xaxis.set_major_formatter(ticker.EngFormatter(unit="s"))
        ax0.yaxis.set_major_formatter(ticker.EngFormatter(unit="V"))
        ax0.set_xlabel("Time (s)")
        ax0.set_ylabel("Voltage (V)")
        ax0.grid()
        ax0.plot(x_time,voltage_points)
       # Plot Current
        ax1.xaxis.set_major_formatter(ticker.EngFormatter(unit="s"))
        ax1.yaxis.set_major_formatter(ticker.EngFormatter(unit="A"))
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Current (A)")
        ax1.grid()
        ax1.plot(x_time,current_points)
        fig.suptitle("Single Point Transient Response")
        plt.show()
        plt.close(fig)

        session.abort() # abort the session to stop any ongoing operations

def _main(argsv):
    parser = argparse.ArgumentParser( description="NI-DCPower Single Point Transient Response Plot") 

    parser.add_argument( "-n","--resource-name",default="NISMU",help="NI-DCPower resource name")
    parser.add_argument( "-op", "--options", default="", help="Driver options string")
    parser.add_argument( "-v","--voltage-level", type=float, default=1.0, help="Voltage level (V)" )
    parser.add_argument( "-vr", "--voltage-level-range", type=float, default=6.0, help="Voltage range (V)" )
    parser.add_argument(  "-m","--measure-record",type=int,default=250,help="Number of measurement samples" )
    parser.add_argument( "-at", "--aperture-time", type=float, default=0, help="Aperture time in seconds" )
    parser.add_argument( "-sd", "--source-delay", type=float, default=0, help="Source delay in seconds" )
    parser.add_argument( "-tr", "--transient-response", default="CUSTOM", help="Transient response mode (SLOW, FAST, NORMAL, or CUSTOM)" )

    # First pass: parse to get transient response mode
    args, remaining_args = parser.parse_known_args(argsv)    
    # Add custom transient parameters only if CUSTOM mode is selected
    if args.transient_response.upper() == 'CUSTOM':
        parser.add_argument( "-vgb", "--voltage-gain-bandwidth", type=float, default=5000, help="Voltage gain bandwidth (for CUSTOM transient)" )
        parser.add_argument( "-vcf", "--voltage-compensation-frequency", type=float, default=50000, help="Voltage compensation frequency (for CUSTOM transient)" )
        parser.add_argument( "-vpzr", "--voltage-pole-zero-ratio", type=float, default=0.16, help="Voltage pole-zero ratio (for CUSTOM transient)" )
        parser.add_argument( "-cgb", "--current-gain-bandwidth", type=float, default=40000, help="Current gain bandwidth (for CUSTOM transient)" )
        parser.add_argument( "-ccf", "--current-compensation-frequency", type=float, default=250000, help="Current compensation frequency (for CUSTOM transient)" )
        parser.add_argument( "-cpzr", "--current-pole-zero-ratio", type=float, default=4, help="Current pole-zero ratio (for CUSTOM transient)" )
        
        # Second pass: parse all arguments including custom parameters
        args = parser.parse_args(argsv)
    else:
        # For non-CUSTOM modes, check if user tried to use custom parameters
        if remaining_args:
            print(f"Warning: Custom transient parameters are only used with -tr CUSTOM mode. Ignoring: {remaining_args}")
        
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
        resource_name = args.resource_name,
        options = args.options,
        voltage_level = args.voltage_level,
        voltage_level_range = args.voltage_level_range,
        measure_record = args.measure_record,
        aperture_time = args.aperture_time,
        source_delay = args.source_delay,
        transient_response = transient_response,
        voltage_gain_bandwidth = args.voltage_gain_bandwidth,
        voltage_compensation_frequency = args.voltage_compensation_frequency,
        voltage_pole_zero_ratio = args.voltage_pole_zero_ratio,
        current_gain_bandwidth = args.current_gain_bandwidth,
        current_compensation_frequency = args.current_compensation_frequency,
        current_pole_zero_ratio = args.current_pole_zero_ratio,
    )


def main():
    """
    Entry point — passes real CLI args to _main().
    """
    _main(sys.argv[1:])


def test_example():
    """
    Simulated hardware test —runs example() with a virtual PXIe-4139.
    """
    options = {'simulate': True, 'driver_setup': {'Model': '4139', 'BoardType': 'PXIe'}}
    example('NISMU', options, 1.0, 6.0, 100, 0.0001, 0.0001, nidcpower.TransientResponse.NORMAL, 5000, 50000, 0.16, 40000, 250000, 4)


def test_main():
    """
    Simulated CLI test —runs _main() with simulate option string.
    """
    cmd_line = [  "-n", "NISMU","-op","Simulate=1,DriverSetup=Model:4139;BoardType:PXIe"]

    _main(cmd_line)
"""  
# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------
"""  
if __name__ == "__main__":
    main()