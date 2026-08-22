import subprocess


print("STEP 1: Normalizing food data...")
subprocess.run(["python", "normalizer.py"], check=True)

print("\nSTEP 2: Matching red-flag ingredients...")
subprocess.run(["python", "matcher.py"], check=True)

print("\nSTEP 3: Calculating scores...")
subprocess.run(["python", "scorer.py"], check=True)

print("\nSTEP 4: Generating JSON...")
subprocess.run(["python", "api_output.py"], check=True)

print("\nPipeline completed successfully!")