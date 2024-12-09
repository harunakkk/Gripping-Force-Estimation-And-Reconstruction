import serial
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
from threading import Lock, Thread
import myo
import joblib
import time
from queue import Queue


# Polynomial coefficients for force calculation (already obtained from force_interp_polynomial.pkl)
params = joblib.load("force_interp_polynomial.pkl")


# Global force_buffers
force_buffers = [deque(maxlen=512) for _ in range(5)]


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
        #self.force_data = force_data

        # Create a buffer for each force sensor using deque
        global force_buffers
        self.force_buffers = force_buffers

        # Create subplots: 8 for EMG + 5 for FSRs = 13 total
        self.fig, self.ax = plt.subplots(13, 1, figsize=(10, 12))

        # EMG Grafikleri
        self.ax_emg = self.ax[:8]
        self.graphs = [ax.plot([], [], label=f"EMG {i+1}")[0] for i, ax in enumerate(self.ax_emg)]
        for i, ax in enumerate(self.ax_emg):
            ax.set_title(f'EMG Sensörü {i+1}')
            ax.set_xlabel('Zaman (s)')
            ax.set_ylabel('Genlik')
            ax.set_ylim(-100, 100)  # Adjust as needed for all graphs
            ax.set_xlim(0, self.n)  # x-limits for time

        # Kuvvet Grafikleri
        self.ax_force = self.ax[8:]
        self.force_plots = []
        for i, ax in enumerate(self.ax_force):
            ax.set_title(f'Kuvvet Sensörü {i+1}')
            ax.set_xlabel('Zaman (s)')
            ax.set_ylabel('Kuvvet (N)')
            ax.set_ylim(0, 30)
            ax.set_xlim(0, self.n)
            self.force_plots.append(ax.plot([], [], label=f"Kuvvet Sensörü {i+1}", color="C" + str(i))[0])
            ax.legend(loc="upper left")
        
        plt.ion()

    def update_plot(self):
        # EMG Grafik Güncellemeleri
        emg_data = self.listener.get_emg_data()
        emg_data = np.array([x[1] for x in emg_data]).T
        for g, data in zip(self.graphs, emg_data):
            if len(data) < self.n:
                data = np.concatenate([np.zeros(self.n - len(data)), data])
            g.set_ydata(data)
            g.set_xdata(np.arange(len(data)))
        
        # Update Force plots
        for i, plot in enumerate(self.force_plots):
            data = np.array(self.force_buffers[i])
            if len(data) < self.n:
                data = np.concatenate([np.zeros(self.n - len(data)), data])
            plot.set_ydata(data)
            plot.set_xdata(np.arange(len(data)))
        
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
def read_force_data(serial_port, force_buffers):
    with open("force_readings.txt", "w") as log_file:  # Open a file for writin
        while True:
            try:
                line = serial_port.readline().decode('utf-8').strip()
                if line:
                    readings = [int(value) for value in line.split(",")]
                    forces = []
                    for reading in readings:
                        voltage = reading / 1023 * 5
                        force = calculate_force(voltage)
                        forces.append(force)

                    # Log the force readings to the file
                        log_file.write(",".join(map(str, forces)) + "\n")
                        log_file.flush()  # Ensure data is written immediately

                    # Update each buffer with the new force value
                    for i, force_value in enumerate(forces):
                        force_buffers[i].append(force_value)
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
    myo.init(sdk_path='D:\Arşiv\Medya\Belgeler\irl\Bitirme Projesi\Gripping-Force-Estimation-And-Reconstruction\myo-sdk-win-0.9.0')  # Replace with the correct SDK path
    hub = myo.Hub()
    listener = EmgCollector(512)
    
    # Open the serial connection to Arduino
    serial_port = serial.Serial('COM5', 115200, timeout=2)  # Update with your Arduino's serial port
    serial_port.flushInput()

    # Create buffers for force data
    global force_buffers

    force_thread = Thread(target=read_force_data, args=(serial_port, force_buffers), daemon=True)
    force_thread.start()

    plot = Plot(listener, force_buffers)

    # Start the Myo event loop
    try:
        with hub.run_in_background(listener.on_event):
            print("Collecting data... Press Ctrl+C to stop.")
            while True:
                plot.update_plot()  # Update EMG and Force plots
                time.sleep(1.0 / 30)  # Limit update rate to 30 FPS

    except KeyboardInterrupt:
        print("Stopping data collection.")
    finally:
        # Ensure proper cleanup
        serial_port.close()
        plt.close('all')



if __name__ == "__main__":
    main()
