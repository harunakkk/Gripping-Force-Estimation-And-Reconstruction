import joblib
import numpy as np

# Load the saved interpolation function
force_interp = joblib.load('force_interp.pkl')
print("Interpolation function loaded.")

# Ard
def analog_to_force(analog_reading, force_interp):
    voltage = (analog_reading / 1023) * 5  # Convert analog to voltage
    #force = (voltage/0.4437)**(1.0/0.301)*0.0098  # Üstel
    #force = (voltage/0.4141)**(1.0/0.3094)*0.0098  # Üstel 2
    force = np.exp((voltage + 1.4955) / 0.7078)*0.0098 # ln
    return force, voltage

# Example usage
analog_reading = int(input())
force, voltage = analog_to_force(analog_reading, force_interp)
print(f"Analog Reading: {analog_reading}, Voltage: {voltage:.2f}V, Force: {force:.2f}N")
