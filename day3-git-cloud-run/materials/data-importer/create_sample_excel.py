from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).parent
SAMPLES_DIR = BASE_DIR / "samples"


def main():
    sales = pd.read_csv(SAMPLES_DIR / "sales_data.csv")
    dealers = pd.read_csv(SAMPLES_DIR / "dealer_master.csv")
    mli_mapping = pd.DataFrame(
        [
            {"model": "Focus", "mli_code": "MLI-100", "segment": "Passenger Car"},
            {"model": "Puma", "mli_code": "MLI-200", "segment": "Crossover"},
            {"model": "Kuga", "mli_code": "MLI-300", "segment": "SUV"},
            {"model": "Mustang Mach-E", "mli_code": "MLI-400", "segment": "Electric"},
        ]
    )
    output_path = SAMPLES_DIR / "monthly_sales.xlsx"

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        sales.to_excel(writer, sheet_name="Sales", index=False)
        dealers.to_excel(writer, sheet_name="Dealers", index=False)
        mli_mapping.to_excel(writer, sheet_name="MLI Mapping", index=False)

    print(f"Created {output_path}")


if __name__ == "__main__":
    main()
