#!/usr/bin/env python3
import serial
import time
import json
import subprocess
import argparse
import threading
from collections import OrderedDict
import requests

# Configuration Section
ipmiip = "192.168.1.60"      # IP address of iLO/IPMI
ipmilogin = "Administrator"  # IPMI username
ipmipassword = "Passw0rd"    # IPMI password
prefan = 120                 # Pre-start cooling at max speed (seconds)
country = "Moscow"           # City for weather data
############################## Weather retreives with ("curl wttr.in/" + country + "?format=%t --silent", shell=True).decode().strip()

try:
    # Get location information
    response = requests.get('https://ipinfo.io', timeout=5)
    response.raise_for_status()
    data = response.json()
    city = data.get('city', country)
    print(f"City found, using {city}")
except requests.exceptions.RequestException as e:
    print(f"Error getting city: {e}, using default: {country}")
    city = country

class FanController:
    def __init__(self, offset, usetemp="warning"):
        self.last_outdoor_temp = "N/A"
        self.last_outdoor_update = 0
        self.serial_port = self._connect_arduino()
        self.MIN_SPEED = self.update_min_speed_initial()
        self.MAX_SPEED = 100
        self.offset = offset / 100.0
        self.usetemp = usetemp.lower()
        
        self.fan_map = {
            1: [0,1,2,3,4,5], 2: [1,2], 3: [3,4],
            4: [1,2], 5: [1,2], 6: [3,4], 7: [3,4],
            8: [0,1,2,3,4,5], 9: [0,5], 10: [1,2,3,4],
            11: [0,5], 12: [0,1,2,3,4,5], 16: [0,5],
            17: [0,5], 18: [0,5], 19: [0,5], 20: [0,5],
            21: [1,2,3,4], 22: [1,2,3,4], 23: [0,5],
            24: [0,5], 25: [0,5], 26: [0,5], 28: [0,5], 29: [0,1,2],
            30: [0,1,2,3,4,5]
        }
        
        self.sensor_overrides = {
            30: {"warning": 100, "critical": 110},
            29: {"warning": 81, "critical": 85}  
        }

        update_thread = threading.Thread(target=self.periodic_update_min_speed, daemon=True)
        update_thread.start()

    def _connect_arduino(self):
        try:
            ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
            time.sleep(2)
            return ser
        except serial.SerialException as e:
            print(f"Error connecting to Arduino: {e}")
            raise

    def get_temperatures(self):
        cmd = (f"ipmitool -I lanplus -H {ipmiip} -U {ipmilogin} -P {ipmipassword} "
               "sensor list 2>/dev/null | grep degrees")
        try:
            output = subprocess.check_output(cmd, shell=True).decode()
            temps = OrderedDict()
            for line in output.split('\n'):
                if 'Temp' in line and '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) < 10:
                        continue
                    try:
                        sensor_num = int(parts[0].split()[1])
                        current_temp = float(parts[1])
                        warning_temp = float(parts[8])
                        critical_temp = float(parts[9])
                        temps[sensor_num] = {
                            'current': current_temp,
                            'warning': warning_temp,
                            'critical': critical_temp
                        }
                    except (ValueError, IndexError):
                        continue
            return temps
        except subprocess.CalledProcessError as e:
            print(f"Error executing IPMI command: {e}")
            return OrderedDict()

    def calculate_required_speed(self, current_temp, base_temp):
        safety_threshold = base_temp * (1 - self.offset)
        if current_temp < safety_threshold:
            return self.MIN_SPEED 
        speed_range = self.MAX_SPEED - self.MIN_SPEED
        temp_range = base_temp - safety_threshold
        speed = self.MIN_SPEED + int((current_temp - safety_threshold) / temp_range * speed_range)
        return max(self.MIN_SPEED, min(self.MAX_SPEED, speed))

    def _draw_ansi_dashboard(self, temps, fan_speeds):
        print("\033[H\033[J", end="")
        
        if time.time() - self.last_outdoor_update > 3600:
            try:
                self.last_outdoor_temp = self.get_outdoor_temperature()
                self.last_outdoor_update = time.time()
            except Exception as e:
                print(f"\033[1;31mError getting outdoor temp: {e}\033[0m")
                self.last_outdoor_temp = "N/A"

        print("\033[1;36m╔════════════════════════════════════════════╗")
        print("\033[1;36m║\033[1;34m SERVER COOLING SYSTEM                      \033[1;36m║")
        print(f"\033[1;36m║ City: {city.ljust(15)} Weather: {str(self.last_outdoor_temp).ljust(4)}°C\033[1;36m      ║")
        print("\033[1;36m╚════════════════════════════════════════════╝\033[0m")
        
        print("\n\033[1;35mTEMPERATURE SENSORS:\033[0m")
        for sensor, data in temps.items():
            current_temp = data['current']
            if sensor in self.sensor_overrides and self.usetemp in self.sensor_overrides[sensor]:
                base_temp = self.sensor_overrides[sensor][self.usetemp]
                override_used = True
            else:
                base_temp = data[self.usetemp]
                override_used = False
            ratio = current_temp / base_temp
            color = self._get_temp_color(ratio)
            bar = self._create_3d_bar(ratio, 20)
            base_type = 'WARN' if self.usetemp == 'warning' else 'CRIT'
            source = "OVERRIDE" if override_used else "IPMI"
            print(f" \033[35m{sensor:2d}:\033[0m {color}{current_temp:5.1f}°C \033[0m{bar} "
                  f"\033[35m[{ratio*100:3.0f}%]\033[0m \033[90m({base_type}: {base_temp}°C, {source})\033[0m")
        
        print("\n\033[1;35mFAN CONTROL:\033[0m")
        for fan, speed in fan_speeds.items():
            ratio = speed / 100
            color = self._get_speed_color(ratio)
            bar = self._create_fan_bar(ratio, 15)
            fan_char = self._get_fan_visual(speed)
            print(f" \033[35mFan{fan}:\033[0m {color}{speed:3d}% \033[0m{bar} "
                  f"{fan_char*3} \033[90m(MIN:{self.MIN_SPEED}% MAX:{self.MAX_SPEED}%)\033[0m")
        
        print("\n\033[1;36m╔══════════════════════════════════════════╗")
        print("\033[1;36m║\033[1;33m Status: \033[32mNORMAL \033[90m| \033[33mUpdated:\033[0m", 
              time.strftime("%H:%M:%S"), "\033[1;36m      ║")
        print("\033[1;36m╚══════════════════════════════════════════╝\033[0m")

    def _get_temp_color(self, ratio):
        if ratio >= 0.9: return "\033[1;31m"
        elif ratio >= 0.82: return "\033[1;33m"
        else: return "\033[1;32m"

    def _get_speed_color(self, ratio):
        if ratio >= 0.8: return "\033[1;31m"
        elif ratio >= 0.5: return "\033[1;33m"
        else: return "\033[1;32m"

    def _create_3d_bar(self, ratio, width):
        filled = int(width * ratio)
        bar = []
        for i in range(width):
            if i < filled:
                if ratio > 0.9: bar.append("\033[41m \033[101m ")
                elif ratio > 0.82: bar.append("\033[43m \033[103m ")
                else: bar.append("\033[42m \033[102m ")
            else: bar.append("\033[100m \033[40m ")
        return ''.join(bar) + '\033[0m'

    def _create_fan_bar(self, ratio, width):
        filled = int(width * ratio)
        symbols = ['▁','▂','▃','▄','▅','▆','▇','█']
        bar = []
        for i in range(width):
            if i < filled:
                level = min(int(ratio * 8), 7)
                bar.append(f"\033[1;36m{symbols[level]}")
            else: bar.append("\033[90m▁")
        return ''.join(bar) + '\033[0m'

    def _get_fan_visual(self, speed):
        if speed > 80: return "🌀"
        elif speed > 50: return "💨"
        else: return "🌬️"

    def control_fans(self):
        temps = self.get_temperatures()
        if not temps:
            print("\033[1;31mERROR: No temperature data received\033[0m")
            return False

        fan_speeds = {fan: self.MIN_SPEED for fan in range(6)}
        for sensor, data in temps.items():
            if sensor not in self.fan_map:
                continue
            current_temp = data['current']
            if sensor in self.sensor_overrides and self.usetemp in self.sensor_overrides[sensor]:
                base_temp = self.sensor_overrides[sensor][self.usetemp]
            else:
                base_temp = data[self.usetemp]
            required_speed = self.calculate_required_speed(current_temp, base_temp)
            for fan in self.fan_map[sensor]:
                if required_speed > fan_speeds[fan]:
                    fan_speeds[fan] = required_speed

        for fan, speed in fan_speeds.items():
            self._send_fan_command(fan, speed)

        self._draw_ansi_dashboard(temps, fan_speeds)
        return True

    def _send_fan_command(self, fan_idx, speed):
        safe_speed = max(self.MIN_SPEED, min(self.MAX_SPEED, speed))
        inverted_speed = 100 - safe_speed
        try:
            cmd = json.dumps({"fan": fan_idx, "speed": inverted_speed})
            self.serial_port.write((cmd + '\n').encode())
            print(f"\033[90m[DEBUG] Fan -> {speed}%\033[0m", end='\r')
        except Exception as e:
            print(f"\033[1;31mERROR: Failed to send command to fan: {e}\033[0m")

    def get_outdoor_temperature(self):
        try:
            output = subprocess.check_output("timeout 10 curl wttr.in/" + country + "?format=%t --silent", shell=True).decode().strip()
            # Ожидается формат, например, '+10°C'
            temp_str = output.replace("°C", "").replace("+", "").strip()
            return float(temp_str)
        except Exception as e:
            raise Exception(f"Ошибка получения уличной температуры: {e}")

    def update_min_speed_initial(self):
        try:
            outdoor_temp = self.get_outdoor_temperature()
            new_min = self.determine_min_speed(outdoor_temp)
            print(f"On startup: outdoor temperature: {outdoor_temp}°C → MIN_SPEED = {new_min}%")
            return new_min
        except Exception as e:
            print(e)
            print("Failed to get temperature on startup, setting MIN_SPEED = 20%")
            return 20

    def determine_min_speed(self, outdoor_temp):
        if outdoor_temp > 15: return 30
        elif -3 <= outdoor_temp <= 5: return 20
        elif outdoor_temp < -3: return 10
        else: return 25

    def periodic_update_min_speed(self):
        while True:
            time.sleep(43200)  # 12 hours
            try:
                outdoor_temp = self.get_outdoor_temperature()
                new_min = self.determine_min_speed(outdoor_temp)
                print(f"\nUpdate: outdoor temperature: {outdoor_temp}°C → MIN_SPEED updated to {new_min}%")
                self.MIN_SPEED = new_min
            except Exception as e:
                print(f"\nError updating MIN_SPEED: {e}\nMIN_SPEED value not changed.")

    def run(self):
        try:
            print("\033[1;32mStarting fan control system\033[0m")
            print(f"\033[1;34mSetting all fans to 100% for {prefan} seconds\033[0m")
            for fan in range(6):
                self._send_fan_command(fan, 100)
            time.sleep(prefan)
            print(f"\033[33mSpeed range: {self.MIN_SPEED}-{self.MAX_SPEED}%\033[0m")
            while True:
                success = self.control_fans()
                if not success:
                    print("\033[1;33mRetrying in 10 seconds...\033[0m")
                    time.sleep(10)
                else:
                    time.sleep(5)
        except KeyboardInterrupt:
            print("\n\033[1;33mResetting fans to minimum speed...\033[0m")
            for fan in range(6):
                self._send_fan_command(fan, self.MIN_SPEED)
        finally:
            if self.serial_port:
                self.serial_port.close()
            print("\033[1;32mFan control system stopped\033[0m")

    def test_mode(self):
        print("\033[1;33mStarting test mode...\033[0m")
        try:
            for speed in [100, 50, 100]:
                print(f"\033[1;34mSetting all fans to {speed}%\033[0m")
                for fan in range(6):
                    self._send_fan_command(fan, speed)
                time.sleep(90)
        except KeyboardInterrupt:
            pass
        finally:
            print("\033[1;32mTest completed\033[0m")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Server fan speed control')
    parser.add_argument('--offset', type=int, default=20, help='Percentage below base temperature (default 20%)')
    parser.add_argument('--usetemp', type=str, default="warning", choices=["warning", "critical"],
                        help='Use warning or critical temperature for calculation')
    parser.add_argument('--test', action='store_true', help='Test mode (check all fans)')
    args = parser.parse_args()

    controller = FanController(args.offset, args.usetemp)
    
    if args.test:
        controller.test_mode()
    else:
        controller.run()
