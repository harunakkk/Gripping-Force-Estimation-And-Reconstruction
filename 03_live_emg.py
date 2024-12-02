import serial
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
from threading import Lock, Thread
import myo
import joblib
import time


# Polynomial coefficients for force calculation (already obtained from force_interp_polynomial.pkl)
params = joblib.load("force_interp_polynomial.pkl")


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

        # Create a figure with 9 subplots (8 for EMG, 1 for Force)
        self.fig, self.ax = plt.subplots(9, 1, figsize=(10, 12))  # 9 total subplots

        # Assign first 8 axes to EMG data, and the last one to Force plot
        self.ax_emg = self.ax[:-1]  # First 8 subplots for EMG
        self.ax_force = self.ax[-1]  # Last subplot for Force
        
        for i, ax in enumerate(self.ax_emg):
            ax.set_title(f'Sensor {i+1}')
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Amplitude')
            ax.set_ylim(-100, 100)  # Adjust as needed for all graphs
            ax.set_xlim(0, self.n)  # x-limits for time

        # Initialize the EMG graphs as empty lines
        self.graphs = [ax.plot(np.arange(self.n), np.zeros(self.n))[0] for ax in self.ax_emg]

        # Initialize Force plot (separate, larger plot)
        self.ax_force.set_title('Force Data (N)')
        self.ax_force.set_xlabel('Time (s)')
        self.ax_force.set_ylabel('Force (N)')
        self.force_plot, = self.ax_force.plot([], [], label="Force (N)", color="red")  # Force plot
        self.ax_force.legend(loc="upper left")
        
        self.ax_force.set_ylim(0, 30)  # Temporary y-limits until data is available
        self.ax_force.set_xlim(0, self.n)  # X-limits for time (0 to n)
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

        # Update Force data plot (only if EMG data is updated)
        force_data = np.array(self.force_data)
        if len(force_data) > 0:
            # Limit force data to the most recent 'n' values, same as with EMG
            if len(force_data) > self.n:
                force_data = force_data[-self.n:]

            # Scroll the force plot similarly to how the EMG data is displayed
            self.force_plot.set_xdata(np.arange(len(force_data)))  # Update x-axis with new length
            self.force_plot.set_ydata(force_data)  # Update y-axis with force data

            # Dynamically adjust the y-axis to fit the range of the force data
            max_force = np.max(force_data)
            min_force = np.min(force_data)

            # Adjust the y-axis to show the full range of force data
            y_margin = 0.1 * (max_force - min_force)  # Optional margin for better visibility
            self.ax_force.set_ylim(min_force - y_margin, max_force + y_margin)  # Set y-limits dynamically


        # Redraw the plot and pause for the next frame (similar to EMG plots)
        plt.draw()
        plt.pause(1.0 / 30)  # Update at 30 FPS

    def main(self):
        while True:
            with data_lock:  # Lock data update synchronization
                self.update_plot()  # Update plot only when both EMG and Force data are ready
            plt.pause(1.0 / 30)


# Shared lock to synchronize force and EMG data collection
data_lock = Lock()


# Function to read force data from Arduino in real-time
def read_force_data(serial_port, force_data):
    while True:
        try:
            line = serial_port.readline().strip()
            if line:
                force_value = int(line)  # Force is read as an integer from Arduino
                # Map the analog reading to force (N)
                voltage = force_value / 1023 * 5  # Convert analog value to voltage
                force = calculate_force(voltage)  # Convert voltage to force using the polynomial fi
                with data_lock:
                    force_data.append(force)  # Append force value to the list
        except Exception as e:
            print(f"Error reading from Arduino: {e}")
            break


# Function to calculate force from voltage using the polynomial fit
def calculate_force(voltage):
    a, b, c, d = params
    force = a * voltage**3 + b * voltage**2 + c * voltage + d
    if force < 0:  # Prevent negative force values
        force = 0
    return force


# Function to map EMG data to force (you can replace this with your specific mapping method)
def map_emg_to_force(emg_data, force_data):
    """
    This function maps EMG data to force values. 
    You could use a regression model or predefined mapping.
    """
    # Example mapping: simple sum of the absolute EMG data
    # This is just an example, you should tailor it to your needs.
    emg_sum = np.sum(np.abs(emg_data))
    force_value = np.interp(emg_sum, [0, 500], [0, max(force_data)])  # Normalize based on the force range
    return force_value


# Main function to initialize Myo SDK and Arduino serial communication
def main():
    # Initialize Myo SDK
    myo.init(sdk_path='../../myo_sdk')  # Replace with the correct SDK path
    hub = myo.Hub()
    listener = EmgCollector(512)
    
    # Open the serial connection to Arduino
    serial_port = serial.Serial('COM5', 9600, timeout=1)  # Update with your Arduino's serial port

    # Start reading force data in a separate thread
    force_data = []  # List to store force data
    force_thread = Thread(target=read_force_data, args=(serial_port, force_data), daemon=True)
    force_thread.start()

    # Start the Myo event loop
    with hub.run_in_background(listener.on_event):
        # Wait for a while while collecting data
        print("Collecting data... Press Ctrl+C to stop.")

        # Plot collected data
        Plot(listener, force_data).main()
        time.sleep(1000)  # Change this to however long you want to collect data for

        # Stop the collection and save the data
        print("Stopping data collection.")



if __name__ == "__main__":
    main()
