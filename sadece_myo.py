import myo
import csv
import time

# CSV File Configuration
CSV_FILENAME = "myo_emg_data.csv"
DURATION_SECONDS = 10  # Time in seconds to collect data

class MyoListener(myo.DeviceListener):
    def __init__(self):
        super().__init__()
        self.data = []
        self.start_time = time.time()
        self.sample_count = 0

    def on_connected(self, event):
        print("Myo Connected!")
        event.device.stream_emg(True)  # Enable EMG streaming

    def on_emg(self, event):
        timestamp = time.time() - self.start_time
        row = [timestamp] + list(event.emg)
        self.data.append(row)
        self.sample_count += 1

    def get_sampling_rate(self):
        elapsed_time = time.time() - self.start_time
        return self.sample_count / elapsed_time if elapsed_time > 0 else 0

def save_to_csv(data):
    with open(CSV_FILENAME, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "EMG1", "EMG2", "EMG3", "EMG4", "EMG5", "EMG6", "EMG7", "EMG8"])
        writer.writerows(data)
    print(f"Data saved to {CSV_FILENAME}")

def main():
    myo.init()
    hub = myo.Hub()
    listener = MyoListener()

    print(f"Collecting data for {DURATION_SECONDS} seconds...")

    try:
        with hub.run_in_background(listener.on_event):
            time.sleep(DURATION_SECONDS)  # Collect data for specified duration
    except KeyboardInterrupt:
        print("Data collection interrupted by user.")
    
    actual_sampling_rate = listener.get_sampling_rate()
    print(f"Data collection complete. Estimated Sampling Rate: {actual_sampling_rate:.2f} Hz")

    save_to_csv(listener.data)

if __name__ == "__main__":
    main()
