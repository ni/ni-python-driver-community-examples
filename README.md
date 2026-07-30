# NI Python Driver Community Examples

The NI Python Driver Community Examples repository provides a collection of community-contributed examples for various NI instrument drivers. This is a complementary resource to the official NI driver documentation, offering real-world usage patterns and advanced techniques for hardware control and data acquisition.

## Key Features & Available Examples

This repository includes examples organized by instrument driver:

- **nidcpower** - SMU (Source Measure Unit) examples
- **nidigital** - Digital Pattern Generation and Measurement examples
- **nidmm**     - Digital Multimeter examples
- **nifgen**    - Function Generator and Arbitrary Waveform Generation examples
- **niscope**   - Oscilloscope examples
- **niswitch**  - Switching Matrix and Relay examples

## Installation

### Prerequisites

Before using these examples, ensure you have the following installed:

- **Python 3.12 or later**

- **NI Instrument Drivers** - Download and Install the required instrument drivers for your hardware from [ni.com/downloads](https://www.ni.com/downloads)

-**NI Python Driver Packages**
   
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

### Python Dependencies
- NI driver Python packages (e.g., `nidcpower`, `nidmm`, `nifgen`, `nidigital`, `niscope`, `niswitch`)

### Hardware Requirements
- NI PXIe chassis with embedded controller or remote connection via MXI-Express (PCIe) or Thunderbolt
- Compatible National Instruments hardware (e.g., PXIe-4139,4147,4162 for DC Power Supply,PXIe-6363 for NI-DAQmx, PXIe-4081 for DMM, PXI-2568 for Switch, PXIe-5163 for Scope, PXIe-6571 for Digital and PXIe-5433 for Fgen and other compatible devices, etc.)
- Appropriate cabling and connectors for your instrument

## Usage Examples

Each example is self-contained and includes comments explaining the key steps.

### Finding Relevant Examples

Each example script in this repository is designed for a specific use case. Check the example file headers and comments to understand:
- What instrument is being used
- What measurements or operations are performed
- Required setup and hardware configuration

