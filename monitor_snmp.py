#!/usr/bin/env python3

import sys
import json
import re
import subprocess
from datetime import datetime
import time

def run_snmpwalk():
    """
    Executes the snmpwalk command and returns its output.
    """
    try:
        result = subprocess.run(
            ["snmpwalk", "-v2c", "-c", "public", "localhost", "1.3.6.1.2.1.1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        return result.stdout
    except Exception as e:
        print(f"Error running snmpwalk: {e}", file=sys.stderr)
        sys.exit(1)


def parse_snmp_output(snmp_output):
    """
    Parses the snmpwalk output into a structured dictionary.
    """
    data = {
        "system": {
            "description": "Unknown",
            "city": "Unknown",
            "outdoor_temp": 0,
            "mode": "warning",
            "last_update": 0
        },
        "fans": {},
        "sensors": {}
    }

    # Regular expressions for parsing
    system_desc_pattern = re.compile(r'iso\.3\.6\.1\.2\.1\.1\.1\.0\s+=\s+STRING:\s+"(.+)"')
    city_pattern = re.compile(r'iso\.3\.6\.1\.2\.1\.1\.5\.0\s+=\s+STRING:\s+"(.+)"')
    outdoor_temp_pattern = re.compile(r'iso\.3\.6\.1\.2\.1\.1\.8\.0\s+=\s+INTEGER:\s+(-?\d+)')
    mode_pattern = re.compile(r'iso\.3\.6\.1\.2\.1\.1\.9\.0\s+=\s+STRING:\s+"(\w+)"')
    last_update_pattern = re.compile(r'iso\.3\.6\.1\.2\.1\.1\.10\.0\s+=\s+INTEGER:\s+(\d+)')
    fan_pattern = re.compile(r'iso\.3\.6\.1\.2\.1\.1\.2\.(\d+)\.0\s+=\s+INTEGER:\s+(\d+)')
    sensor_pattern = re.compile(r'iso\.3\.6\.1\.2\.1\.1\.4\.(\d+)\.(\d)\.0\s+=\s+INTEGER:\s+(\d+)')

    for line in snmp_output.splitlines():
        # System description
        if match := system_desc_pattern.match(line):
            data["system"]["description"] = match.group(1)
        # City
        elif match := city_pattern.match(line):
            data["system"]["city"] = match.group(1)
        # Outdoor temperature
        elif match := outdoor_temp_pattern.match(line):
            data["system"]["outdoor_temp"] = int(match.group(1))
        # Mode (warning/critical)
        elif match := mode_pattern.match(line):
            data["system"]["mode"] = match.group(1)
        # Last update time
        elif match := last_update_pattern.match(line):
            data["system"]["last_update"] = int(match.group(1))
        # Fans
        elif match := fan_pattern.match(line):
            fan_num = int(match.group(1))
            fan_speed = int(match.group(2))
            data["fans"][f"fan{fan_num}"] = fan_speed
        # Sensors
        elif match := sensor_pattern.match(line):
            sensor_num = int(match.group(1))
            sensor_type = int(match.group(2))
            sensor_value = int(match.group(3))

            # Initialize the sensor if it hasn't been added yet
            if sensor_num not in data["sensors"]:
                data["sensors"][sensor_num] = {"current": 0, "warning": 0, "critical": 0}

            # Update sensor values
            if sensor_type == 0:  # Current temperature
                data["sensors"][sensor_num]["current"] = sensor_value
            elif sensor_type == 1:  # Warning threshold
                data["sensors"][sensor_num]["warning"] = sensor_value
            elif sensor_type == 2:  # Critical threshold
                data["sensors"][sensor_num]["critical"] = sensor_value

    return data


def format_sensor_table(sensors):
    """
    Formats sensor data into a table with borders.
    """
    table = [
        "╔════════╦══════════╦══════════════╦════════════╗",
        "║ Sensor ║ Current  ║ Warning      ║ Critical   ║",
        "╠════════╬══════════╬══════════════╬════════════╣"
    ]

    for sensor, values in sensors.items():
        current = values["current"]
        warning = values["warning"]
        critical = values["critical"]

        # Color highlighting
        current_color = "\033[31m" if current >= critical else "\033[33m" if current >= warning else "\033[32m"
        warning_color = "\033[33m" if warning > 0 else ""
        critical_color = "\033[31m" if critical > 0 else ""

        row = (
            f"║ {sensor:<6} ║ {current_color}{current:<8}\033[0m ║ "
            f"{warning_color}{warning:<12}\033[0m ║ {critical_color}{critical:<10}\033[0m ║"
        )
        table.append(row)

    table.append("╚════════╩══════════╩══════════════╩════════════╝")
    return "\n".join(table)


def format_table(parsed_data):
    """
    Formats the data into a readable text table.
    """
    table = []

    # System information
    system = parsed_data["system"]
    last_update = datetime.fromtimestamp(system["last_update"]).strftime("%Y-%m-%d %H:%M:%S")
    table.append("=== System Information ===")
    table.append(f"Description: {system['description']}")
    table.append(f"City: {system['city']}")
    table.append(f"Outdoor Temperature: {system['outdoor_temp']}°C")
    table.append(f"Mode: {system['mode']}")
    table.append(f"Last Update: {last_update}")
    table.append("")

    # Fans
    table.append("=== Fan Speeds ===")
    for fan, speed in parsed_data["fans"].items():
        color = "\033[31m" if speed > 80 else "\033[33m" if speed > 50 else "\033[32m"
        table.append(f"{fan}: {color}{speed}%\033[0m")
    table.append("")

    # Sensors
    table.append("=== Sensor Data ===")

    # Filter out sensors where all values are 0
    filtered_sensors = {
        sensor: values
        for sensor, values in parsed_data["sensors"].items()
        if any(value != 0 for value in values.values())
    }

    if filtered_sensors:
        table.append(format_sensor_table(filtered_sensors))
    else:
        table.append("No sensor data available.")

    return "\n".join(table)


def main():
    """
    Main function for auto-updating data.
    """
    try:
        while True:
            # Clear the terminal
            print("\033[H\033[J", end="")

            # Execute snmpwalk
            snmp_output = run_snmpwalk()

            # Parse SNMP data
            parsed_data = parse_snmp_output(snmp_output)

            # Format data into a table
            formatted_table = format_table(parsed_data)

            # Print the table
            print(formatted_table)

            # Delay before the next update
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nThe program has been terminated by the user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
