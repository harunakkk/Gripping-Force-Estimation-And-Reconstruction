import joblib

# Load the saved interpolation function
force_interp = joblib.load('force_interp.pkl')
print("Interpolation function loaded.")

# Ard
def analog_to_force(analog_reading, force_interp):
    voltage = (analog_reading / 1023) * 5  # Convert analog to voltage
    force = force_interp(voltage)  # Interpolate to get force
    return force, voltage

# Example usage
analog_reading = 709
force, voltage = analog_to_force(analog_reading, force_interp)
print(f"Analog Reading: {analog_reading}, Voltage: {voltage:.2f}V, Force: {force:.2f}N")
