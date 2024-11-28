import serial
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Function to read data from Arduino
def read_fsr_data(ser):
    line = ser.readline().decode('utf-8').strip()  # Read a line and decode it
    return [int(val) for val in line.split(',')]  # Split CSV data into integers

# Function to fit a curve (power law) to the FSR data
def fit_curve(analog_values, forces):
    def power_law(x, a, b):
        return a * np.power(x, -b)

    params, _ = curve_fit(power_law, analog_values, forces)
    return params, power_law

# Main function to collect data and fit the curve
def main():
    ser = serial.Serial('COM3', 9600, timeout=1)  # Adjust COM port as needed
    analog_values = []
    forces = []  # Replace with actual known force values (e.g., [0, 1, 2, 3...])
    
    print("Collecting FSR data... Press Ctrl+C to stop.")
    try:
        while len(analog_values) < 50:  # Collect 50 samples for calibration
            fsr_readings = read_fsr_data(ser)
            print(f"FSR Readings: {fsr_readings}")
            analog_values.append(fsr_readings[0])  # Example: Only use first FSR for now
            forces.append(0.5 * len(analog_values))  # Dummy force data; replace with real values

    except KeyboardInterrupt:
        print("Data collection stopped.")

    # Fit the curve
    params, power_law = fit_curve(np.array(analog_values), np.array(forces))
    print(f"Fitted Curve Parameters: a={params[0]:.2f}, b={params[1]:.2f}")

    # Plot the data
    plt.scatter(analog_values, forces, label="Data Points")
    plt.plot(analog_values, power_law(np.array(analog_values), *params), color='red', label="Fitted Curve")
    plt.xlabel("Analog Reading (0-1023)")
    plt.ylabel("Force (N)")
    plt.legend()
    plt.show()

if __name__ == "__main__":
    main()
