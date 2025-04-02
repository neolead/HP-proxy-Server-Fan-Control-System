# HP-proxy-Server-Fan-Control-System

## English Documentation

### Overview
This project allows you to control server fans based on temperature readings obtained from IPMI sensors. The system uses an Arduino Nano for controlling the fan speeds, which are adjusted based on dynamic thresholds set in the Python script. The Arduino reads analog signals from the motherboard's temperature sensors and adjusts the fan speeds accordingly.

### Features
🌀 **Intelligent fan control** based on IPMI temperature sensors  
🌡️ **Dynamic speed adjustment** using warning/critical temperature thresholds  
🌦️ **Weather-based minimum speed** (adjusts for seasonal temperature changes)  
🖥️ **Beautiful ANSI console dashboard** with real-time monitoring  
⚙️ **Manual temperature overrides** for specific sensors  
🧪 **Test mode** for fan verification  

### Requirements
- Python 3.x  
- ipmitool installed and configured  
- Arduino connected via USB (`/dev/ttyUSB0`)  
- Python packages: `pyserial`, `requests`  

### Hardware Setup
1. **Build the Arduino Nano circuit**:
   - Use **6 low-pass filters** (2kOhm and 1uF should be sufficient) connected to the **A0-A5 analog inputs** on the Arduino Nano.
   - Connect the **6 PWM-capable wires** from fans these analog inputs.
   - Connect the **6 PWM-capable pins (D3, D5, D6, D9, D10, D11)** on the Arduino to the **fan control wires**.

2. **Arduino Nano pin assignments**:
   - Pin 3: CPU fan
   - Pin 5: Front fan
   - Pin 6: Rear fan
   - Pin 9: HDD fan
   - Pin 10: PCIe fan
   - Pin 11: Auxiliary fan

### Installation
```
git clone https://github.com/your-repo/server-fan-control.git  
cd server-fan-control  
pip install pyserial requests  
chmod +x fan_controller.py  
```  

### Configuration
Edit these variables at the top of the script:
```
ipmiip = "192.168.1.60"       # IPMI IP address  
ipmilogin = "Administrator"   # IPMI username  
ipmipassword = "PassW0rd"     # IPMI password  
prefan = 120                  # Initial full-speed cooling (seconds)  
country = "Moscow"            # Your city for weather data  
```  

### Usage
```
./fan_controller.py [--offset PERCENT] [--usetemp warning|critical] [--test]  
```  

#### Options:
- `--offset`: Safety margin below base temperature (default: 20%)  
- `--usetemp`: Temperature threshold to use: "warning" or "critical" (default: warning)  
- `--test`: Run in test mode (cycles through fan speeds)  

### Customization
- **Fan mapping**: Modify `fan_map` to match your server's sensor-fan relationships  
- **Temperature overrides**: Add custom thresholds in `sensor_overrides`  
- **Speed parameters**: Adjust `MIN_SPEED` logic in `determine_min_speed()`  

---

### `hp_fan_proxy_arduino.ino` Documentation

This is the Arduino sketch that controls the fans based on commands sent from the Python server. It is compiled and uploaded to the Arduino Nano, which then communicates with the server and controls the fan speeds accordingly.

#### Features:
- Reads and stores PWM values for each fan from EEPROM.
- Sets initial fan speeds based on stored PWM values.
- Allows updates to fan speeds based on incoming JSON commands from the server.
- Supports error handling for invalid fan indices.
- Provides debug output over serial.

#### Variables:
- `NUM_FANS`: Number of fans to control (6 in this case).
- `MIN_PWM`: Minimum PWM value (10, roughly 12% speed).
- `MAX_PWM`: Maximum PWM value (255, 100% speed).
- `DEFAULT_PWM`: Default PWM value for first-time initialization (50).

#### Fan Pins:
The fan pins are assigned to the following digital pins on the Arduino Nano:
- Pin 3: CPU fan
- Pin 5: Front fan
- Pin 6: Rear fan
- Pin 9: HDD fan
- Pin 10: PCIe fan
- Pin 11: Auxiliary fan

#### Setup:
- Initializes serial communication at a baud rate of 115200.
- Loops through each fan, reading and setting PWM values stored in EEPROM.
- If no valid value is stored in EEPROM, it sets the default PWM value.
- Outputs initialization status for each fan to the serial monitor.

#### Loop:
- Continuously checks for incoming serial commands (in JSON format).
- Calls the `processCommand` function when a valid command is received.

#### Command Processing (`processCommand`):
- The incoming command is expected to be a JSON string with `fan` and `speed` fields.
- The `fan` field specifies which fan to control (from 0 to 5).
- The `speed` field specifies the desired speed from 0 to 100 (percentage).
- Speed is constrained to the range of 10-100%.
- The speed is converted to a PWM value and applied to the selected fan.

### License MIT License
Credits: https://www.michu-it.com/portfolio/hp-proliant-custom-fan-proxy/
![IMG_20200807_135436-2048x1536](https://github.com/user-attachments/assets/0f86a7ca-e618-451c-a2db-fd36003581c4)
![IMG_20200806_190644-scaled](https://github.com/user-attachments/assets/bc2f7d58-bc1c-4c2a-b663-688a404f61ce)
![IMG_20200806_182002-2048x1536](https://github.com/user-attachments/assets/d0e9a4e4-2f5d-4468-8cf1-d3521f32941d)

# HP-proxy-Server-Fan-Control-System

## Русская документация

### Обзор
Этот проект позволяет управлять вентиляторами сервера на основе показаний температурных датчиков IPMI. Система использует Arduino Nano для контроля скорости вентиляторов, которые регулируются на основе динамических порогов, установленных в Python-скрипте. Arduino считывает аналоговые сигналы с температурных датчиков материнской платы и регулирует скорость вентиляторов.

### Возможности
🌀 **Интеллектуальное управление вентиляторами** на основе данных IPMI  
🌡️ **Динамическая регулировка скорости** с использованием температурных порогов предупреждения/критического состояния  
🌦️ **Погодозависимая минимальная скорость** (адаптация к сезонным изменениям температуры)  
🖥️ **Красивый ANSI интерфейс** с мониторингом в реальном времени  
⚙️ **Ручные настройки температур** для отдельных датчиков  
🧪 **Тестовый режим** для проверки вентиляторов  

### Требования
- Python 3.x  
- Установленный и настроенный ipmitool  
- Arduino, подключенная через USB (`/dev/ttyUSB0`)  
- Python пакеты: `pyserial`, `requests`

### Схема подключения
1. **Собрать схему на Arduino Nano**:
   - Используйте **6 низкочастотных фильтров** (2kOhm и 1uF будут достаточны), подключенных к **аналоговым входам A0-A5** на Arduino Nano.
   - Подключите **6 проводов от вентиляторов** к этим аналоговым входам.
   - Подключите **6 PWM-выходов (D3, D5, D6, D9, D10, D11)** на Arduino к **проводам управления вентиляторами**.

2. **Назначение пинов Arduino Nano**:
   - Pin 3: CPU fan
   - Pin 5: Front fan
   - Pin 6: Rear fan
   - Pin 9: HDD fan
   - Pin 10: PCIe fan
   - Pin 11: Auxiliary fan

### Установка
&&&
git clone https://github.com/your-repo/server-fan-control.git  
cd server-fan-control  
pip install pyserial requests  
chmod +x fan_controller.py  
&&&

### Настройка
Отредактируйте переменные в начале скрипта:
&&&
ipmiip = "192.168.1.60"       # IP-адрес IPMI  
ipmilogin = "Administrator"   # Логин IPMI  
ipmipassword = "PassW0rd"     # Пароль IPMI  
prefan = 120                  # Время начального охлаждения (сек)  
country = "Moscow"            # Ваш город для погодных данных  
&&&

### Использование
&&&
./fan_controller.py [--offset ПРОЦЕНТ] [--usetemp warning|critical] [--test]  
&&&

#### Параметры:
- `--offset`: Запас ниже базовой температуры (по умолчанию: 20%)  
- `--usetemp`: Использовать порог "warning" или "critical" (по умолчанию: warning)  
- `--test`: Тестовый режим (проверка вентиляторов)  

### Кастомизация
- **Привязка вентиляторов**: Настройте `fan_map` под вашу серверную платформу  
- **Температурные исключения**: Добавьте свои пороги в `sensor_overrides`  
- **Скорости вращения**: Измените логику `MIN_SPEED` в `determine_min_speed()`  

---

### Документация для `hp_fan_proxy_arduino.ino`

Этот скетч Arduino управляет вентиляторами на основе команд, отправляемых с сервера Python. Он компилируется и загружается в Arduino Nano, который затем взаимодействует с сервером и регулирует скорость вентиляторов.

#### Возможности:
- Считывает и сохраняет значения PWM для каждого вентилятора из EEPROM.
- Устанавливает начальную скорость вентиляторов на основе сохранённых значений PWM.
- Позволяет обновлять скорости вентиляторов на основе входящих JSON-команд от сервера.
- Обрабатывает ошибки для неверных индексов вентиляторов.
- Выводит отладочную информацию через последовательный порт.

#### Переменные:
- `NUM_FANS`: Количество вентиляторов для управления (в данном случае 6).
- `MIN_PWM`: Минимальное значение PWM (10, примерно 12% от скорости).
- `MAX_PWM`: Максимальное значение PWM (255, 100% от скорости).
- `DEFAULT_PWM`: Значение PWM для первой инициализации (50).

#### Пины для вентиляторов:
Пины для вентиляторов назначены следующим образом:
- Pin 3: CPU fan
- Pin 5: Front fan
- Pin 6: Rear fan
- Pin 9: HDD fan
- Pin 10: PCIe fan
- Pin 11: Auxiliary fan

#### Setup:
- Инициализирует последовательную коммуникацию со скоростью 115200 бод.
- Проходит через каждый вентилятор, считывает и устанавливает значения PWM, сохранённые в EEPROM.
- Если значение невалидно, устанавливается значение по умолчанию.
- Выводит информацию о статусе инициализации для каждого вентилятора в монитор последовательного порта.

#### Loop:
- Постоянно проверяет наличие входящих команд по последовательному порту (в формате JSON).
- Вызывает функцию `processCommand`, когда получена валидная команда.

#### Обработка команд (`processCommand`):
- Ожидается, что входная команда будет строкой JSON с полями `fan` и `speed`.
- Поле `fan` указывает, какой вентилятор управлять (от 0 до 5).
- Поле `speed` указывает желаемую скорость в пределах от 0 до 100 (проценты).
- Скорость ограничена диапазоном от 10 до 100%.
- Скорость преобразуется в значение PWM и применяется к выбранному вентилятору.

### Лицензия  
MIT License - свободное использование с указанием авторства  
Credits: https://www.michu-it.com/portfolio/hp-proliant-custom-fan-proxy/
