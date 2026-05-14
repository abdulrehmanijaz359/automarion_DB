import sys
sys.path.append('middleware')
from blocking_logic import BlockingLogic
from relocation import Relocation

bl = Relocation()
blk = BlockingLogic()

print("\n🧪 TEST — Build sequence for retrieving A(2,2)")
print("   B(2,2) and C(2,2) are occupied\n")

# Get blocking slots
accessible, blocking, message = blk.check_access('A', 2, 2)

# Build the full sequence
steps, temp = bl.build_sequence(
    command_id    = 1,
    target_level  = 'A',
    target_row    = 2,
    target_col    = 2,
    blocking_slots = blocking
)

print("📋 Full command sequence:")
print("-" * 60)
for step in steps:
    if step['action'] == 'HOME':
        print(f"  Step {step['step_number']:2} → 🏠 HOME")
    elif step['action'] == 'PICK':
        print(f"  Step {step['step_number']:2} → 🤏 PICK  from {step['from_level']}({step['from_row']},{step['from_col']})")
    elif step['action'] == 'PLACE':
        print(f"  Step {step['step_number']:2} → 📥 PLACE to   {step['to_level']}({step['to_row']},{step['to_col']})")

print("-" * 60)
print(f"  Total steps: {len(steps)}")

# Save to database
print("\n💾 Saving sequence to database...")
bl.save_sequence(steps)