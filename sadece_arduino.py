import serial
import csv
import time

# Configuration
SERIAL_PORT = "COM3"  # Change this to match your Arduino port (e.g., "/dev/ttyUSB0" on Linux/Mac)
BAUD_RATE = 115200  # Match this with Arduino's Serial.begin()
CSV_FILENAME = "force_sensor_data.csv"
DURATION_SECONDS = 10  # Time in seconds to collect data

def read_serial_and_write_csv():
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser, open(CSV_FILENAME, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Sensor1", "Sensor2", "Sensor3", "Sensor4", "Sensor5"])  # CSV header

            start_time = time.time()
            sample_count = 0

            print(f"Collecting data for {DURATION_SECONDS} seconds...")
            
            while time.time() - start_time < DURATION_SECONDS:
                if ser.in_waiting > 0:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()
                    readings = line.split(",")

                    if len(readings) == 5 and all(value.isdigit() for value in readings):
                        timestamp = time.time() - start_time
                        row = [timestamp] + [int(value) for value in readings]
                        writer.writerow(row)
                        sample_count += 1

            elapsed_time = time.time() - start_time
            actual_sampling_rate = sample_count / elapsed_time
            print(f"Data collection complete. Estimated Sampling Rate: {actual_sampling_rate:.2f} Hz")
            print(f"Data saved to {CSV_FILENAME}")

    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    read_serial_and_write_csv()
