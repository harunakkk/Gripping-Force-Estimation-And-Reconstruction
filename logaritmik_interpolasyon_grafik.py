import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Load data from CSV file.
# Adjust skip_header parameter depending on whether your CSV file has a header row.
data = np.genfromtxt('plot-data.csv', delimiter=',', skip_header=1)
force = data[:, 0]    # First column: force (grams)
voltage = data[:, 1]  # Second column: voltage (volts)

# Define a logarithmic model: Voltage = a * ln(Force) + b
def log_model(f, a, b):
    return a * np.log(f) + b

# Define a power-law model: Voltage = a * (Force)^b
def power_model(f, a, b):
    return a * np.power(f, b)

# Fit the logarithmic model to the data
params_log, cov_log = curve_fit(log_model, force, voltage)
a_log, b_log = params_log

# Fit the power-law model to the data
params_power, cov_power = curve_fit(power_model, force, voltage)
a_power, b_power = params_power

# Generate a fine grid of force values for plotting the fitted curves
force_fit = np.linspace(np.min(force), np.max(force), 100)
voltage_log_fit = log_model(force_fit, a_log, b_log)
voltage_power_fit = power_model(force_fit, a_power, b_power)

# Print fitted parameters
print("Logarithmic model: Voltage = a * ln(Force) + b")
print("Fitted parameters: a = {:.4f}, b = {:.4f}".format(a_log, b_log))
print("\nPower-law model: Voltage = a * (Force)^b")
print("Fitted parameters: a = {:.4f}, b = {:.4f}".format(a_power, b_power))

# Plot the original data and the fitted curves
plt.figure(figsize=(8, 6))
plt.scatter(force, voltage, color='red', label='Data')
plt.plot(force_fit, voltage_log_fit, label='Logarithmic Fit', linewidth=2)
plt.plot(force_fit, voltage_power_fit, label='Power-law Fit', linewidth=2, linestyle='--')
plt.xlabel('Force (grams)')
plt.ylabel('Voltage (volts)')
plt.title('Force vs Voltage Calibration')
plt.legend()
plt.grid(True)
plt.show()
