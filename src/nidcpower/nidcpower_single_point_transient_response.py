"""
NI-DCPower Single Point - Transient Response Plot

Comment:
--------
This example demonstrates how to capture and plot the transient response
of an NI-DCPower SMU while operating in Single Point Source Mode.

The example:
    - Configures the SMU for DC voltage sourcing
    - Configures continuous measurements using Measure Trigger
    - Captures voltage and current samples
    - Plots voltage vs time and current vs time
    - Displays transient response characteristics

Tested Hardware:
    - PXIe-4139
    - PXIe-4145 (expected to work)

HOW TO RUN:
-----------

i. From terminal (with default values):

    python nidcpower_single_point_transient_response.py

ii. From terminal (with custom values):

    python nidcpower_single_point_transient_response.py \
        -n "PXI1Slot2" \
        -v 1.0 \
        -r 6.0 \
        -m 250

iii. To simulate without hardware:

    python nidcpower_single_point_transient_response.py \
        -op "Simulate=1,DriverSetup=Model:4145;BoardType:PXIe"
"""

import argparse
import sys
import time

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import nidcpower


def example(
    resource_name,
    options,
    voltage_level,
    voltage_range,
    measure_record
):
    """
    Core measurement logic — opens session, configures,
    sources, measures, and plots transient response.

    Args:
        resource_name (str):
            NI-DCPower resource name.

        options (str):
            Driver option string.

        voltage_level (float):
            Output voltage level in volts.

        voltage_range (float):
            Voltage range in volts.

        measure_record (int):
            Number of samples to acquire.

    Returns:
        list:
            List of fetched measurements.
    """

    voltage_points = []
    current_points = []

    plt.rcParams["figure.figsize"] = [7.50, 3.50]
    plt.rcParams["figure.autolayout"] = True

    fig, (ax0, ax1) = plt.subplots(
        nrows=2,
        figsize=(7, 9.6)
    )

    with nidcpower.Session(
        resource_name=resource_name,
        channels=0,
        reset=True,
        options=options,
        independent_channels=True
    ) as session:

        # ----------------------------------------------------
        # Setup
        # ----------------------------------------------------

        session.source_mode = nidcpower.SourceMode.SINGLE_POINT
        session.output_function = nidcpower.OutputFunction.DC_VOLTAGE

        session.voltage_level = voltage_level
        session.voltage_level_range = voltage_range

        session.aperture_time_units = (
            nidcpower.ApertureTimeUnits.SECONDS
        )

        session.aperture_time = 0
        session.source_delay = 0

        session.transient_response = (
            nidcpower.TransientResponse.NORMAL
        )

        session.measure_when = (
            nidcpower.MeasureWhen.ON_MEASURE_TRIGGER
        )

        session.exported_start_trigger_output_terminal = (
            f"/{resource_name}/PXI_Trig0"
        )

        session.measure_trigger_type = (
            nidcpower.TriggerType.DIGITAL_EDGE
        )

        session.digital_edge_measure_trigger_input_terminal = (
            f"/{resource_name}/PXI_Trig0"
        )

        session.measure_record_length_is_finite = False
        session.measure_record_length = measure_record
        session.measure_buffer_size = 20000000

        session.output_enabled = True

        # ----------------------------------------------------
        # Commit
        # ----------------------------------------------------

        session.commit()

        # ----------------------------------------------------
        # Initiate
        # ----------------------------------------------------

        session.initiate()

        # ----------------------------------------------------
        # Action
        # ----------------------------------------------------

        start_time = time.time()

        measurements = session.channels[0].fetch_multiple(
            count=session.measure_record_length
        )

        end_time = time.time()

        print(
            f"Generation Time: "
            f"{end_time - start_time:.6f} seconds"
        )

        print(
            f"Measurements Acquired: {len(measurements)}"
        )

        print(
            f"Aperture Time: "
            f"{session.aperture_time:.2e} seconds"
        )

        if session.aperture_time > 0:
            print(
                f"Sample Rate: "
                f"{1/session.aperture_time:.2e} S/s"
            )

        transient_settings = {
            "Voltage Gain Bandwidth":
                session.voltage_gain_bandwidth,
            "Voltage Compensation Frequency":
                session.voltage_compensation_frequency,
            "Voltage Pole Zero Ratio":
                session.voltage_pole_zero_ratio,
            "Current Gain Bandwidth":
                session.current_gain_bandwidth,
            "Current Compensation Frequency":
                session.current_compensation_frequency,
            "Current Pole Zero Ratio":
                session.current_pole_zero_ratio
        }

        print("\nTransient Response Settings:")
        print(transient_settings)

        # ----------------------------------------------------
        # Store Data for Plotting
        # ----------------------------------------------------

        for measurement in measurements:
            voltage_points.append(measurement[0])
            current_points.append(measurement[1])

        x_time = [
            session.aperture_time * x
            for x in range(len(measurements))
        ]

        # ----------------------------------------------------
        # Plot Voltage
        # ----------------------------------------------------

        ax0.xaxis.set_major_formatter(
            ticker.EngFormatter(unit="s")
        )

        ax0.yaxis.set_major_formatter(
            ticker.EngFormatter(unit="V")
        )

        ax0.set_xlabel("Time (s)")
        ax0.set_ylabel("Voltage (V)")
        ax0.grid()

        ax0.plot(
            x_time,
            voltage_points
        )

        # ----------------------------------------------------
        # Plot Current
        # ----------------------------------------------------

        ax1.xaxis.set_major_formatter(
            ticker.EngFormatter(unit="s")
        )

        ax1.yaxis.set_major_formatter(
            ticker.EngFormatter(unit="A")
        )

        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Current (A)")
        ax1.grid()

        ax1.plot(
            x_time,
            current_points
        )

        fig.suptitle(
            "Single Point Transient Response"
        )

        plt.show()

        session.abort()

    return measurements


def _main(argsv):
    parser = argparse.ArgumentParser(
        description="NI-DCPower Single Point Transient Response Plot"
    )

    parser.add_argument(
        "-n",
        "--resource-name",
        default="NISMU1",
        help="NI-DCPower resource name"
    )

    parser.add_argument(
        "-op",
        "--options",
        default="",
        help="Driver options string"
    )

    parser.add_argument(
        "-v",
        "--voltage-level",
        type=float,
        default=1.0,
        help="Voltage level (V)"
    )

    parser.add_argument(
        "-r",
        "--voltage-range",
        type=float,
        default=6.0,
        help="Voltage range (V)"
    )

    parser.add_argument(
        "-m",
        "--measure-record",
        type=int,
        default=250,
        help="Number of measurement samples"
    )

    args = parser.parse_args(argsv)

    example(
        args.resource_name,
        args.options,
        args.voltage_level,
        args.voltage_range,
        args.measure_record
    )


def main():
    """
    Entry point — passes real CLI args to _main().
    """
    _main(sys.argv[1:])


def test_example():
    """
    Simulated hardware test —
    runs example() with a virtual PXIe-4145.
    """

    example(
        resource_name="NISMU1",
        options="Simulate=1,DriverSetup=Model:4145;BoardType:PXIe",
        voltage_level=1.0,
        voltage_range=6.0,
        measure_record=100
    )


def test_main():
    """
    Simulated CLI test —
    runs _main() with simulate option string.
    """

    cmd_line = [
        "-n", "NISMU1",
        "-op",
        "Simulate=1,DriverSetup=Model:4145;BoardType:PXIe"
    ]

    _main(cmd_line)


# ------------------------------------------------------------
# Script execution starts here
# ------------------------------------------------------------

if __name__ == "__main__":
    main()