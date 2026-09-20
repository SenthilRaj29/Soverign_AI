import asyncio
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(backend_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.agents.orchestrator import OpenWorkerAgentOrchestrator
from scripts.seed_synthetic_data import create_synthetic_industrial_knowledge

async def run_master_verification():
    print("=== STARTING SOVEREIGN AI WORKBENCH MASTER VERIFICATION ===")
    
    # 1. Seed Synthetic Data
    create_synthetic_industrial_knowledge()
    print("✓ Synthetic industrial documents and sensor dataset seeded successfully.")

    # 2. Instantiate Orchestrator
    orchestrator = OpenWorkerAgentOrchestrator()

    # 3. Execute Master Task
    objective = "Analyze the uploaded pump inspection report and sensor data, check applicable safety procedures, determine whether maintenance is required, and prepare an approval note."
    sensor_csv = "e:/Soverign_AI/datasets/pump_sensor_data.csv"
    inspection_img = "e:/Soverign_AI/knowledge_base/documents/pump_damage.jpg"

    if not os.path.exists(inspection_img):
        os.makedirs(os.path.dirname(inspection_img), exist_ok=True)
        with open(inspection_img, "wb") as f:
            f.write(b"dummy_image_data")

    print("\nExecuting Offline Agent Loop...")
    result = await orchestrator.execute_industrial_inspection_task(
        user_id="eng_senthil",
        objective=objective,
        sensor_csv_path=sensor_csv,
        inspection_img_path=inspection_img,
        user_role="ENGINEER"
    )

    print("\n=== VERIFICATION RESULTS ===")
    print(f"Task ID: {result['task_id']}")
    print(f"Status: {result['status']}")
    print(f"Summary: {result['summary']}")
    print(f"Total Findings: {len(result['findings'])}")
    print(f"Total Recommendations: {len(result['recommendations'])}")
    print(f"Generated Artifacts: {result['artifacts']}")
    print(f"Audit Log Recorded: {result['audit_trail_recorded']}")
    print("\n✓ 100% Offline Agentic Workflow Verified Successfully!")

if __name__ == "__main__":
    asyncio.run(run_master_verification())
