import os

def create_synthetic_industrial_knowledge():
    base_dir = "e:/Soverign_AI/knowledge_base/documents"
    os.makedirs(base_dir, exist_ok=True)

    # 1. Safety Manual
    safety_doc = """
NOVA INDUSTRIAL SYSTEMS — SAFETY & LOCKOUT/TAGOUT (LOTO) PROCEDURE
Document Ref: NOVA-SOP-2024-08
Classification: Confidential - Internal Engineering Use Only
Department: Safety & Operations

1. PURPOSE & SCOPE
This document outlines mandatory safety protocol for servicing high-pressure centrifugal pumps and turbine drive shafts. 

2. LOCKOUT / TAGOUT (LOTO) MANDATORY STEPS
Step 2.1: Isolate primary electrical power breaker at Substation-4. Apply lock #LOTO-RED.
Step 2.2: Close suction and discharge valves V-101 and V-102. Depressurize housing to 0 PSI.
Step 2.3: Verify zero movement of impeller.

3. TEMPERATURE & VIBRATION OPERATIONAL LIMITS
- Normal Operating Temperature: 60°C to 75°C.
- Warning Threshold (Action Required): 80°C.
- Critical Shutdown Threshold: 85°C. Continuous operation above 85°C risks bearing seizure and casing fracture.
- Vibration Limit: RMS vibration above 4.5 mm/s indicates severe mechanical mis-alignment or shaft pitting. Immediate maintenance required.
"""
    with open(os.path.join(base_dir, "NOVA_Safety_SOP_LOTO.txt"), "w", encoding="utf-8") as f:
        f.write(safety_doc)

    # 2. Equipment Specifications & Maintenance Manual
    maint_doc = """
NOVA INDUSTRIAL SYSTEMS — CENTRIFUGAL PUMP CP-9000 MAINTENANCE MANUAL
Document Ref: NOVA-SPEC-CP9000
Classification: Proprietary
Department: Maintenance Engineering

1. EQUIPMENT SPECIFICATIONS
Model: CP-9000 Industrial Heavy-Duty Centrifugal Pump
Rated Flow Rate: 1200 L/min
Maximum Operating Pressure: 15 BAR

2. INSPECTION PROCEDURE FOR CRACKING & CASING DAMAGE
Visual characteristics consistent with surface damage, hairline fatigue fractures, or cavitation pitting on the outer volute casing must be tagged immediately. 
If visual pitting or surface rust width exceeds 2.0mm, replacement of housing assembly CP-9000-HSG is required.

3. SENSOR CALIBRATION & MAINTENANCE APPROVAL NOTE
When temperature sensor T-201 exceeds 85°C concurrently with vibration sensor V-302 exceeding 4.5 mm/s:
An Emergency Maintenance Approval Note must be prepared by the lead engineer and authorized by the Plant Manager before restarting operation.
"""
    with open(os.path.join(base_dir, "NOVA_Pump_CP9000_Maintenance_Manual.txt"), "w", encoding="utf-8") as f:
        f.write(maint_doc)

    # 3. Sample Industrial Sensor CSV Data
    csv_data = """timestamp,temperature,vibration,pressure,flow_rate,status
2026-09-06T10:00:00,72.4,2.1,14.2,1190,NORMAL
2026-09-06T10:05:00,74.1,2.3,14.1,1185,NORMAL
2026-09-06T10:10:00,78.8,3.2,13.9,1160,WARNING
2026-09-06T10:15:00,86.5,4.8,13.2,1110,CRITICAL_VIOLATION
2026-09-06T10:20:00,89.2,5.4,12.8,1050,CRITICAL_VIOLATION
2026-09-06T10:25:00,91.7,5.9,12.1,980,CRITICAL_VIOLATION
"""
    dataset_dir = "e:/Soverign_AI/datasets"
    os.makedirs(dataset_dir, exist_ok=True)
    with open(os.path.join(dataset_dir, "pump_sensor_data.csv"), "w", encoding="utf-8") as f:
        f.write(csv_data)

if __name__ == "__main__":
    create_synthetic_industrial_knowledge()
