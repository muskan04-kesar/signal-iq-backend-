from backend.simulation.engine import simulation_engine
from backend.simulation.models import Vehicle, SignalState
import time

print("--- Testing Signal Compliance ---")

# Setup: Clear vehicles
simulation_engine.vehicles = []

print("Spawning test vehicle approaching S34 from S1...")
v = Vehicle(
    id="test-v",
    edge_source="S1", 
    edge_target="S34", 
    position=180.0, # distance 226, stop offset 35, start observing from 180
    speed=10.0, 
    target_speed=10.0,
    type="car"
)
simulation_engine.vehicles.append(v)

# Get S34
s34 = simulation_engine.intersections["S34"]

# Test 1: Signal is RED
print("\nTest 1: Signal is RED")
s34.nsSignal = SignalState.RED
s34.ewSignal = SignalState.RED
simulation_engine._update_vehicles(0.1) # Step simulation
print(f"Vehicle Speed: {v.speed}")

if v.speed < 10.0:
    print("SUCCESS: Vehicle started stopping at RED light.")
else:
    print(f"FAILURE: Vehicle did not stop. Speed={v.speed}")

# Test 2: Signal is GREEN
print("\nTest 2: Signal is GREEN")
s34.nsSignal = SignalState.GREEN
s34.ewSignal = SignalState.GREEN
simulation_engine._update_vehicles(0.5) # Step simulation
print(f"Vehicle Speed: {v.speed}")

if v.speed > 0.0:
    print("SUCCESS: Vehicle resumed at GREEN light.")
else:
    print(f"FAILURE: Vehicle did not resume. Speed={v.speed}")
