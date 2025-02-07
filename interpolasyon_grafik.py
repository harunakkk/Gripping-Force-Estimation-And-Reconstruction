import numpy as np
from scipy.optimize import curve_fit
import csv
import joblib
import matplotlib.pyplot as plt

# Define the 3rd degree polynomial function for fitting.
def poly_fit(x, a, b, c, d):
    return a * x**3 + b * x**2 + c * x + d

def initialize_fsr_mapping(file_path):
    forces = []
    voltages = []
    
    # Read data from CSV file provided by the manufacturer
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            # First column: force in grams, second column: voltage in volts.
            forces.append(float(row[0]))
            voltages.append(float(row[1]))
    
    # Convert force from grams to Newtons (1 gram ~ 0.0098 N)
    forces_newtons = np.array(forces) * 0.0098
    voltages = np.array(voltages)

    # Perform a 3rd degree polynomial fitting
    params, _ = curve_fit(poly_fit, voltages, forces_newtons, maxfev=10000)
    joblib.dump(params, 'force_interp_polynomial.pkl')
    print("Polynomial function saved to 'force_interp_polynomial.pkl'.")
    
    # Generate a range of voltage values for plotting the fitted curve.
    x_fit = np.linspace(min(voltages), max(voltages), 1000)
    y_fit = poly_fit(x_fit, *params)

    # Plot the original data and the fitted polynomial.
    plt.figure(figsize=(8, 6))
    plt.scatter(voltages, forces_newtons, color='blue', label='Manufacturer Data')
    plt.plot(x_fit, y_fit, color='red', label='3rd Degree Polynomial Fit')
    plt.xlabel('Voltage (V)')
    plt.ylabel('Force (N)')
    plt.title('Polynomial Fit of Force vs. Voltage')
    plt.legend()
    plt.grid(True)
    plt.show()

# Call the function with your CSV file path.
initialize_fsr_mapping('./FSR 402 10k ohm RM Manufacturer Graph Data.csv')
