import numpy as np
from scipy.optimize import curve_fit
import csv
import joblib

# Define a function to model the relationship between voltage and force
# We will use a 3rd degree polynomial fit (you can adjust the degree if necessary)
def poly_fit(x, a, b, c, d):
    return a * x**3 + b * x**2 + c * x + d

# Read data from CSV and perform polynomial fitting
def initialize_fsr_mapping(file_path):
    forces = []
    voltages = []
    
    # Read data from the manufacturer's CSV
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            forces.append(float(row[0]))  # Force in grams
            voltages.append(float(row[1]))  # Voltage in volts
    
    # Convert forces to Newtons
    forces_newtons = np.array(forces) * 0.0098
    voltages = np.array(voltages)

    # Perform polynomial fitting (3rd degree)
    params, _ = curve_fit(poly_fit, voltages, forces_newtons, maxfev=10000)

    # Save the fitted polynomial coefficients
    joblib.dump(params, 'force_interp_polynomial.pkl')
    print("Polynomial function saved to 'force_interp_polynomial.pkl'.")

# Call the function to create the polynomial fit and save it
initialize_fsr_mapping('./FSR 402 10k ohm RM Manufacturer Graph Data.csv')
