# Timecode Generator App

This application provides a versatile solution for generating and distributing various types of timecode, including LTC (Linear Timecode), MTC (MIDI Timecode), and Art-Net Timecode. The application has two operating modes: Master Mode and Slave Mode.

## Features

### Master Mode
In Master Mode, the application acts as a server that broadcasts timecode to all connected clients. This centralizes the generation and distribution of timecode across a network.

### Slave Mode
In Slave Mode, the application functions as a client that connects to the Master server to receive the timecode. This is useful when multiple synchronized devices are desired.

## Supported Timecode Types

The application is capable of generating and sending the following types of timecode:

- **LTC (Linear Timecode):** Commonly used in the film and audio industry to synchronize devices.
- **MTC (MIDI Timecode):** Widely used in musical environments to synchronize MIDI equipment.
- **Art-Net Timecode:** Used in the Art-Net protocol for synchronizing lighting and stage devices.

