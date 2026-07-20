# NI Python Driver Community Examples

The NI Python Driver Community Examples repository provides a collection of community-contributed and official examples for various NI instrument drivers. This is a complementary resource to the official NI driver documentation, offering real-world usage patterns and advanced techniques for hardware control and data acquisition.

## Key Features & Available Examples

This repository includes examples organized by instrument driver:

- **nidcpower** - DC Power Supply and SMU (Source Measure Unit) examples
- **nidigital** - Digital Pattern Generation and Measurement examples
- **nidmm** - Digital Multimeter examples
- **nifgen** - Function Generator and Arbitrary Waveform Generation examples
- **niscope** - Oscilloscope examples
- **niswitch** - Switching Matrix and Relay examples

## Installation

### Prerequisites

Before using these examples, ensure you have the following installed:

- **Python 3.6 or later**
- **NI Drivers** - Install the required instrument drivers for your hardware from [ni.com/downloads](https://www.ni.com/downloads)

-**Install Python Driver Packages**
   
   Install the NI driver packages for the instruments you're using:
   ```bash
   # Example: Install nidcpower and nidmm drivers
   pip install nidcpower
   pip install nidmm
   ```
   
   For a complete list of available NI Python drivers, visit [PyPI](https://pypi.org) and search for `ni` package names.

## Requirements

### System Requirements
- Windows 10/11, macOS, or Linux
- Administrator/sudo privileges may be required for NI driver installation
- Compatible NI instruments connected via USB, Ethernet, or GPIB

### Python Dependencies
- NI driver Python packages (e.g., `nidcpower`, `nidmm`, `nifgen`, `nidigital`, `niscope`, `niswitch`)

### Hardware Requirements
- Compatible National Instruments hardware (e.g., PXIe-4162, 4139 for DC Power Supply, NI-DAQmx compatible devices, etc.)
- Appropriate cabling and connectors for your instrument

## Usage Examples

Each example is self-contained and includes comments explaining the key steps.

### Running an Example

1. Navigate to the desired driver directory:
   ```bash
   cd src/nidcpower
   ```

2. Run the example script:
   ```bash
   python example_script.py
   ```

### Finding Relevant Examples

Each example script in this repository is designed for a specific use case. Check the example file headers and comments to understand:
- What instrument is being used
- What measurements or operations are performed
- Required setup and hardware configuration

