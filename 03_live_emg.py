import serial
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
from threading import Lock, Thread
import myo
import joblib
import time

# Load the force interpolation function from the .pkl file
force_interp = joblib.load('force_interp.pkl')

class EmgCollector(myo.DeviceListener):
    """
    Collects EMG data in a queue with *n* maximum number of elements.
    """

    def __init__(self, n):
        self.n = n
        self.lock = Lock()
        self.emg_data_queue = deque(maxlen=n)

    def get_emg_data(self):
        with self.lock:
            return list(self.emg_data_queue)

    # myo.DeviceListener

    def on_connected(self, event):
        event.device.stream_emg(True)

    def on_emg(self, event):
        with self.lock:
            self.emg_data_queue.append((event.timestamp, event.emg))


class Plot(object):

    def __init__(self, listener, force_data):
        self.n = listener.n
        self.listener = listener
        self.force_data = force_data
        self.fig = plt.figure()
        self.axes = [self.fig.add_subplot(8, 1) for i in range(1, 9)]
        [(ax.set_ylim([-100, 100])) for ax in self.axes]
        self.graphs = [ax.plot(np.arange(self.n), np.zeros(self.n))[0] for ax in self.axes]
        self.force_graph = self.fig.add_subplot(9, 1)  # Additional graph for force data
        self.force_plot, = self.force_graph.plot([], [], label="Force (N)", color="red")
        plt.ion()

    def update_plot(self):
        # Update EMG data plots
        emg_data = self.listener.get_emg_data()
        emg_data = np.array([x[1] for x in emg_data]).T
        for g, data in zip(self.graphs, emg_data):
            if len(data) < self.n:
                # Fill the left side with zeroes.
                data = np.concatenate([np.zeros(self.n - len(data)), data])
            g.set_ydata(data)

        # Update Force data plot
        force_data = np.array(self.force_data)
        self.force_plot.set_xdata(np.arange(len(force_data)))
        self.force_plot.set_ydata(force_data)

        plt.draw()

    def main(self):
        while True:
            self.update_plot()
            plt.pause(1.0 / 30)


# Function to read force data from Arduino in real-time
def read_force_data(serial_port, force_data):
    while True:
        try:
            line = serial_port.readline().decode('utf-8').strip()
            if line:
                force_value = int(line)  # Force is read as an integer from Arduino
                # Map the analog reading to force (N)
                force = force_interp(force_value / 1023 * 5)  # Convert analog to voltage and apply the interpolation
                force_data.append(force)  # Append force value to the list
        except Exception as e:
            print(f"Error reading from Arduino: {e}")
            break


# Main function to initialize Myo SDK and Arduino serial communication
def main():
    # Initialize Myo SDK
    myo.init(sdk_path='../../myo_sdk')  # Replace with the correct SDK path
    hub = myo.Hub()
    listener = EmgCollector(512)
    
    # Open the serial connection to Arduino
    serial_port = serial.Serial('COM3', 9600, timeout=1)  # Update with your Arduino's serial port

    # Start reading force data in a separate thread
    force_data = []  # List to store force data
    force_thread = Thread(target=read_force_data, args=(serial_port, force_data), daemon=True)
    force_thread.start()

    # Start the Myo event loop
    with hub.run_in_background(listener.on_event):
        print("Waiting for Myo to connect ...")
        device = listener.wait_for_single_device(2)
        if not device:
            print("No Myo connected after 2 seconds.")
            return

        print("Hello, Myo! Requesting RSSI ...")
        device.request_rssi()

        # Wait for a while while collecting data
        print("Collecting data... Press Ctrl+C to stop.")
        time.sleep(10)  # Change this to however long you want to collect data for

        # Stop the collection and save the data
        print("Stopping data collection.")

    # Plot collected data
    Plot(listener, force_data).main()

if __name__ == "__main__":
    main()
