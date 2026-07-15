#!/usr/bin/env python3
"""NI-FGEN Software Trigger Example.

This example demonstrates how to configure software triggering modes for the signal
generator.

Multiple waveforms (sine, square, ramp up, ramp down, sawtooth) are created and
configured in sequence mode. By pressing the 'Q' key, a software trigger is sent
to cycle through the different waveforms, and the output reflects each change.

Note: Not all trigger modes are available on all NI signal generators.

HOW TO RUN:
-----------
i.   From terminal (with default values):
        python nifgen_software_trigger.py

ii.  From terminal (with custom values):
        python nifgen_software_trigger.py \
            -n "PXI1Slot11" -sr 1e6 -ns 100 -g 1.0 -o 0.0 -lc 1

iii. To simulate without hardware:
    python nifgen_software_trigger.py \
        -op "Simulate=1,DriverSetup=Model:5433 (1CH);BoardType:PXIe"

"""

# Module imports
import argparse    # For parsing command-line arguments
import sys         # For accessing command-line arguments via sys.argv
import time        # For time-based delays
import math        # For trigonometric waveform calculations
import keyboard    # For detecting keyboard input

import nifgen      # NI-FGEN instrument driver


def generate_waveforms(number_of_samples):
    """
    Generate multiple waveform data arrays.

    Args:
        number_of_samples (int):
            Number of samples for each waveform
            eg: 100 → 100 samples per waveform

    Returns:
        dict: Dictionary containing 'waveforms' list and 'names' list
            - waveforms: List of waveform data arrays [sine, square, ramp_up, ramp_down, sawtooth]
            - names: List of waveform names for display
    """
    # Creation of different waveform data
    sine_wave = [math.sin(math.pi * 2 * x / number_of_samples) for x in range(number_of_samples)] # Sine wave generation using sine function
    square_wave = [1.0 if x < (number_of_samples / 2) else -1.0 for x in range(number_of_samples)] # Square wave generation using conditional logic
    ramp_up = [x / number_of_samples for x in range(number_of_samples)] # Ramp up generation using linear scaling
    ramp_down = [-1.0 * x for x in ramp_up] # Ramp down generation by negating ramp up values
    sawtooth_wave = [2 * (x - int(x)) - 1 for x in [x / (number_of_samples / 2) for x in range(number_of_samples)]] # Sawtooth wave generation using fractional part calculation

    return {
        'waveforms': [sine_wave, square_wave, ramp_up, ramp_down, sawtooth_wave],
        'names': ['Sine', 'Square', 'Ramp Up', 'Ramp Down', 'Sawtooth']
    }


def example(
    resource_name, fgen_options,
    sample_rate, number_of_samples,
    gain, offset, loop_count):
    """
    Configure FGEN with multiple waveforms in sequence mode and respond to software triggers.

    Args:
        resource_name (str):
            NI-FGEN device identifier (eg: "PXI1Slot11")

        fgen_options (str or dict):
            FGEN driver options, eg: "" for real HW or simulate string for simulation

        sample_rate (float):
            Arbitrary waveform sample rate (S/s)
            eg: 1e6 → 1 MS/s

        number_of_samples (int):
            Number of samples for each waveform
            eg: 100 → 100 samples

        gain (float):
            Sequence waveform gain scaling factor
            REASON: Allows signal amplitude adjustment without regenerating waveforms
            eg: 1.0 → full amplitude, 0.5 → half amplitude

        offset (float):
            Sequence waveform DC offset voltage
            REASON: Enables testing with signal bias/offset without code changes
            eg: 0.0 → no offset, 1.0 → +1V offset

        loop_count (int):
            Number of times each waveform repeats per trigger
            REASON: Configurable repetition allows testing various duty cycles and sequences
            eg: 1 → play once, 3 → play three times per trigger

    Returns:
        None — results are printed to console and real-time output is generated
    """

    # -> Initialize FGEN Session
    # - Opens communication with the signal generator
    # - 'with' ensures automatic cleanup of session resources
    with nifgen.Session(
        resource_name=resource_name,
        reset_device=True,
        options=fgen_options,
    ) as session:

        # -> Generate Waveform Data
        # - Create multiple waveform shapes (sine, square, ramps, sawtooth)
        waveform_data = generate_waveforms(number_of_samples)
        waveforms = waveform_data['waveforms']
        waveform_names = waveform_data['names']

        # -> Configure FGEN Settings
        # - output_mode        → SEQ (Sequence mode for multiple waveforms)
        # - arb_sample_rate    → Custom sample rate for waveforms
        # - trigger_mode       → Specified trigger mode (BURST, CONTINUOUS, etc.)
        # - start_trigger_type → Trigger type (SOFTWARE_EDGE for user-triggered)
        session.output_mode = nifgen.OutputMode.SEQ
        session.arb_sample_rate = sample_rate

        # Set trigger mode and start trigger type directly
        session.trigger_mode = nifgen.TriggerMode.BURST
        session.start_trigger_type = nifgen.StartTriggerType.SOFTWARE_EDGE

        # -> Create Waveforms and Sequence
        # - Create waveform handles for each waveform
        # - Configure them in a sequence for looped playback
        waveform_handles = []
        for waveform in waveforms:
            waveform_handles.append(session.create_waveform(waveform_data_array=waveform))

        # Create sequence with configurable loop count per waveform
        sequence_handle = session.create_arb_sequence(
            waveform_handles,
            loop_counts_array=[loop_count] * len(waveforms)
        )
        session.configure_arb_sequence(
            sequence_handle=sequence_handle,
            gain=gain,
            offset=offset
        )

        # -> Initiate and Monitor
        # - Start signal generation
        # - Monitor keyboard for 'Q' key to send software triggers
        try:
            session.initiate()
            print(f"FGEN Session initiated on {resource_name}")
            print(f"Sample Rate: {sample_rate} S/s")
            print(f"Number of Samples: {number_of_samples}")
            print(f"Gain: {gain}")
            print(f"Offset: {offset} V")
            print(f"Loop Count: {loop_count}")
            print("\nPress 'Q' key to send a software trigger and cycle waveforms.")
            print("Available waveforms: " + ", ".join(waveform_names))
            print("Press Ctrl + C to end the program.\n")

            # Monitor for 'Q' key press to send software trigger
            while True:
                if keyboard.is_pressed('q'):             # Check if 'Q' key is pressed
                    session.send_software_edge_trigger(
                        trigger=nifgen.Trigger.START,
                        trigger_id=""
                    )                                    # Send software trigger to start waveform sequence
                    print("Software trigger sent - waveform cycling...")
                    time.sleep(5.0)
        except KeyboardInterrupt:
            session.abort()                              # Abort the session to clean up resources
            session.reset()                              # Reset the AWG to its default state
            print("\nProgram ended by user")             # Inform the user that the program has ended due to user interrupt


def _main(argsv):
    """Parses command-line arguments and calls example() with the parsed values."""
    parser = argparse.ArgumentParser(description='NI-FGEN Software Trigger Example')
    parser.add_argument('-n',  '--resource-name',      default='PXI1Slot11', help='FGEN resource name')
    parser.add_argument('-sr',  '--sample-rate',        default=1e6,   type=float, help='Arbitrary waveform sample rate (S/s)')
    parser.add_argument('-ns',  '--number-of-samples',  default=100,   type=int,   help='Number of samples per waveform')
    parser.add_argument('-g',   '--gain',               default=1.0,   type=float, help='Sequence waveform gain scaling factor (amplitude)')
    parser.add_argument('-o',   '--offset',             default=0.0,   type=float, help='Sequence waveform DC offset voltage (V)')
    parser.add_argument('-lc',  '--loop-count',         default=1,     type=int,   help='Number of times each waveform repeats per trigger')
    parser.add_argument('-op',  '--option-string',      default='',    type=str,   help='FGEN driver option string, eg: "Simulate=1, DriverSetup=Model:5412"')
    args = parser.parse_args(argsv)

    example(
        resource_name=args.resource_name,
        fgen_options=args.option_string,
        sample_rate=args.sample_rate,
        number_of_samples=args.number_of_samples,
        gain=args.gain,
        offset=args.offset,
        loop_count=args.loop_count,
    )


def main():
    """Entry point — passes real CLI args to _main()."""
    _main(sys.argv[1:])


def test_example():
    """Simulated hardware test — runs example() with a simulated PXIe-5433 (no real HW needed)."""
    options = "Simulate=1,DriverSetup=Model:5433 (1CH);BoardType:PXIe"
    example("PXI1Slot11", options, 1e6, 100, 1.0, 0.0, 1, options)


def test_main():
    """Simulated CLI test — runs _main() with simulate option string."""
    cmd_line = ["-op", "Simulate=1,DriverSetup=Model:5433 (1CH);BoardType:PXIe"]
    _main(cmd_line)


# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------
if __name__ == '__main__':
    main()
