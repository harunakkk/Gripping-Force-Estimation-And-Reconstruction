import numpy as np
from scipy.interpolate import interp1d
import csv
import joblib

# Üretici firma verisine göre fonksiyon oluşturma. Bu kodun sadece bir kez çalıştırılması yeterli.
def initialize_fsr_mapping(file_path):
    forces = []
    voltages = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            forces.append(float(row[0]))  # Force in grams
            voltages.append(float(row[1]))  # Voltage in volts

    # Convert force to Newtons
    forces_newtons = np.array(forces) * 0.0098
    voltages = np.array(voltages)

    # Create interpolation function
    force_interp = interp1d(voltages, forces_newtons, kind='linear', fill_value="extrapolate")
    
    # Save the function to a file
    joblib.dump(force_interp, 'force_interp.pkl')
    print("Interpolation function saved to 'force_interp.pkl'.")

initialize_fsr_mapping('.\FSR 402 10k ohm RM Manufacturer Graph Data.csv') # Bu veri üretici firmanın sağladığı datasheet'teki grafik baz alınarak WebPlotDigitizer ile elde edilmiştir.
