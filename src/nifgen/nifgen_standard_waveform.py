#!/usr/bin/env python3
"""NI-FGEN Standard Waveform Generation Example.

This example demonstrates how to generate standard waveforms using an NI-FGEN device
in Standard Function mode. Various waveform types (sine, square, triangle, ramp, etc.)
can be generated with configurable amplitude and frequency parameters.

HOW TO RUN:
-----------
i. From terminal (with default values):
    python nifgen_standard_waveform.py

ii. From terminal (with custom values):
    python nifgen_standard_waveform.py \
        -n "PXI1Slot11" -w "sine" -a 2.0 -f 1e6

iii. To simulate without hardware:
    python nifgen_standard_waveform.py \
        -op "Simulate=1,DriverSetup=Model:5433 (1CH);BoardType:PXIe"

"""

# Module imports
import argparse          # argparse is used to parse command line arguments
import sys               # sys is used to access command line arguments
import time              # time is used to keep the program running until the user interrupts with Ctrl + c

import nifgen            # for FGEN Instrument control
        

def example(resource_name, waveform_type, amplitude, frequency, options):
    """
    Core waveform generation logic — opens session, configures output,
    and generates the specified waveform.

    Args:
        resource_name (str): NI-FGEN resource name.
        waveform_type (str): Type of waveform to generate (sine, square, triangle, etc.).
        amplitude (float): Waveform amplitude in volts.
        frequency (float): Waveform frequency in Hz.
        options (str): Driver initialization options.
    """

    # Dictionary with the different waveforms that can be outputted in Standard Function mode.
    waveforms = {"sine": nifgen.Waveform.SINE,
                 "square": nifgen.Waveform.SQUARE,
                 "triangle": nifgen.Waveform.TRIANGLE,
                 "dc": nifgen.Waveform.DC,
                 "ramp_up": nifgen.Waveform.RAMP_UP,
                 "ramp_down": nifgen.Waveform.RAMP_DOWN,
                 "noise": nifgen.Waveform.NOISE}

    # 'with' ensures automatic cleanup of session resources
    with nifgen.Session(resource_name=resource_name, options=options) as session:

        # Set the output mode to Standard Function.
        session.output_mode = nifgen.OutputMode.FUNC
        # Configure the waveform type, amplitude, and frequency.
        session.configure_standard_waveform(waveform=waveforms[waveform_type],
                                            amplitude=amplitude,
                                            frequency=frequency)
        # Enable the output and initiate the waveform generation.
        session.output_enabled = True
        
        # Initiate the session to start waveform generation.
        session.initiate()

        # Display waveform configuration parameters.
        print("\nWaveform Configuration:") # Prints a header for the waveform configuration section
        print("Waveform Type: {}".format(waveform_type))  # Prints the selected waveform type
        print("Amplitude: {} V".format(amplitude))  # Prints the configured amplitude in volts
        print("Frequency: {} Hz".format(frequency))  # Prints the configured frequency in hertz
        print("\nWaveform generation started. Press Ctrl + c to end the program")  # Informs the user that waveform generation has started and how to stop it

        # Keep the program running until the user interrupts with Ctrl + c.
        try:
            if "Simulate=1" in (options or "") or not sys.stdin.isatty():
                # Avoid hanging automated/non-interactive runs and avoid busy-waiting.
                time.sleep(0.1)
            else:
                while True:  # Keep the program running until interrupted
                    time.sleep(0.1)
        except KeyboardInterrupt:  # Handle user interrupt (Ctrl + c)
            pass
        finally:
            session.output_enabled = False  # Disable the output to stop waveform generation
            session.abort()  # Abort the session to clean up resources
            
            print("Waveform generation ended")  # Inform the user that waveform generation has ended


def _main(argsv):
    """Command line interface — parses arguments and calls example()."""
    parser = argparse.ArgumentParser(description="NI-FGEN Standard Waveform Generation Example")

    parser.add_argument("-n",   "--resource-name",         default="PXI1Slot11",    help="NI-FGEN resource name")
    parser.add_argument("-w",   "--waveform-type", default="sine", choices=["sine", "square", "triangle", "dc", "ramp_up", "ramp_down", "noise"], help="Waveform type (sine, square, triangle, dc, ramp_up, ramp_down, noise)")
    parser.add_argument("-a",   "--amplitude",  type=float, default=2.0,           help="Waveform amplitude in volts")
    parser.add_argument("-f",   "--frequency",  type=float, default=1e6,           help="Waveform frequency in Hz")
    parser.add_argument("-op",  "--options",                default="",            help="Driver initialization options")
    args = parser.parse_args(argsv)

    example(
        resource_name=args.resource_name,
        waveform_type=args.waveform_type,
        amplitude=args.amplitude,
        frequency=args.frequency,
        options=args.options)


def main():
    """Entry point — passes real CLI args to _main()."""
    _main(sys.argv[1:])


def test_example():
    """Simulated hardware test — runs example() with a simulated PXIe-5433 (no real HW needed)."""
    options = "Simulate=1,DriverSetup=Model:5433 (1CH);BoardType:PXIe"
    example("PXI1Slot11", "sine", 2.0, 1e6, options)


def test_main():
    """Simulated CLI test — runs _main() with simulate option string."""
    cmd_line = ["-op", "Simulate=1,DriverSetup=Model:5433 (1CH);BoardType:PXIe"]
    _main(cmd_line)


# ------------------------------------------------------------
# Script execution starts here 
# ------------------------------------------------------------
if __name__ == '__main__':
    main()
