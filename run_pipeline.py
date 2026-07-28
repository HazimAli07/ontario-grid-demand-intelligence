from grid_intelligence.pipeline import run_pipeline


if __name__ == "__main__":
    summary = run_pipeline()
    print("Ontario Grid Demand Intelligence pipeline complete")
    for key, value in summary.items():
        print(f"{key}: {value}")

