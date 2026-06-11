import argparse
import nidigital
import os
import sys


def example(resource_name,options,force_current=100e-6,voltage_high_limit=0.8, voltage_low_limit=0.0):
    voltages = []

    with nidigital.Session(resource_name=resource_name, reset_device=False, options=options) as session:

        # Store directory path
        dir = os.path.join(os.path.dirname(__file__))

        # Load pin map
        pin_map_filename = os.path.join(dir, 'PinMap.pinmap')
        session.load_pin_map(file_path=pin_map_filename)

        # Set all pins to PPMU mode
        session.channels["All_Pins"].selected_function = nidigital.SelectedFunction.PPMU
        session.channels["All_Pins"].ppmu_aperture_time_units = nidigital.PPMUApertureTimeUnits.SECONDS
        session.channels["All_Pins"].ppmu_aperture_time = 20e-6

        # Configure Power pins to 0 V
        session.channels["Power"].ppmu_output_function = nidigital.PPMUOutputFunction.VOLTAGE
        session.channels["Power"].ppmu_current_limit_range = 10e-3
        session.channels["Power"].ppmu_voltage_level = 0
        session.channels["Power"].ppmu_source()

        # Configure DUT pins
        session.channels["DUTPins"].ppmu_current_level_range = 128e-6
        session.channels["DUTPins"].ppmu_voltage_limit_low = -1.5
        session.channels["DUTPins"].ppmu_voltage_limit_high = 1.5
        session.channels["DUTPins"].ppmu_output_function = nidigital.PPMUOutputFunction.CURRENT
        session.channels["DUTPins"].ppmu_current_level = force_current

        pin_info = session.channels["DUTPins"].get_pin_results_pin_information()

        print("Starting Continuity test")

        # Test positive and negative clamp diodes
        for i in range(2):
            session.channels["DUTPins"].ppmu_source()
            voltages.append(session.channels["DUTPins"].ppmu_measure(measurement_type=nidigital.PPMUMeasurementType.VOLTAGE))

            for j in range(len(pin_info)):

                if abs(voltage_low_limit) <= abs(voltages[i][j]) <= abs(voltage_high_limit):
                    pass_fail = "Pass"
                else:
                    pass_fail = "Fail"

                print(
                    f'{pin_info[j][0]} on Site {pin_info[j][1]} '
                    f'@ {session.channels["DUTPins"].ppmu_current_level:.3e} A: '
                    f'{voltages[i][j]:.3f} V --> {pass_fail}'
                )

            # Reverse current for negative clamp diode
            session.channels["DUTPins"].ppmu_current_level *= -1

        # Disconnect all pins
        session.selected_function = nidigital.SelectedFunction.DISCONNECT

    print("Continuity test complete")


def _main(argsv):

    parser = argparse.ArgumentParser(description='Continuity test using NI Digital Pattern Instrument',formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-n', '--resource-name', default='PXI1Slot2', help='NI Digital Pattern Instrument resource name')
    parser.add_argument('-s', '--simulate', default='False', choices=['True', 'False'], help='Run using simulated hardware')
    parser.add_argument('-fc', '--force-current', default=100e-6, type=float, help='PPMU force current')
    parser.add_argument('-vhl', '--voltage-high-limit', default=0.8, type=float, help='PPMU voltage high limit')
    parser.add_argument('-vll', '--voltage-low-limit', default=0.0, type=float, help='PPMU voltage low limit')
    args = parser.parse_args(argsv)

    example(resource_name=args.resource_name,
        options='Simulate=1, DriverSetup=Model:6571' if args.simulate == 'True' else '',
        force_current=args.force_current,
        voltage_high_limit=args.voltage_high_limit,
        voltage_low_limit=args.voltage_low_limit)

def main():
    _main(sys.argv[1:])


def test_example():

    resource_name = "NI6570"
    options = { "simulate": True, "driver_setup": {   "Model": "6571" }}
    force_current=100e-6, 
    voltage_high_limit=0.8,
    voltage_low_limit=0.0

    example(resource_name=resource_name, options=options, force_current=force_current, voltage_high_limit=voltage_high_limit, voltage_low_limit=voltage_low_limit)


if __name__ == '__main__':
    main()

