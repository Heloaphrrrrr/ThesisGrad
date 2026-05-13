import argparse
from pathlib import Path

from app.app_settings import load_config_from_yaml
from app.data_access.csv_source import CSVDataSource
from app.services.pipeline_service import DataCleaningPipelineService
from app.services.report_service import ReportService
from app.services.fix_service import FixService
from app.data_seeding.dirty_data_seeder import DirtyDataSeeder
from app.utils import (
    normalize_empty_strings,
    ensure_columns_exist,
    ensure_transaction_id,
    add_bank_derived_features,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="ML Data Cleaning Pipeline CLI"
    )

    parser.add_argument("--input", required=True, help="Input CSV file path")
    parser.add_argument("--output", default="outputs", help="Output directory")
    parser.add_argument("--config", default=None, help="YAML config path")

    parser.add_argument("--report", action="store_true", help="Generate issue report")
    parser.add_argument("--apply-fixes", action="store_true", help="Apply suggested fixes")
    parser.add_argument(
        "--mode",
        choices=["auto", "conservative", "interactive"],
        default="conservative",
        help="Fixing mode",
    )

    parser.add_argument("--seed-dirty", action="store_true", help="Generate dirty data")
    parser.add_argument("--seed-rate", type=float, default=0.2, help="Dirty data rate")

    return parser.parse_args()


def main():
    args = parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = load_config_from_yaml(args.config)

    source = CSVDataSource(
        input_path=args.input,
        output_dir=str(output_dir),
    )

    df = source.read()
    df = normalize_empty_strings(df)
    df = add_bank_derived_features(df)
    df = ensure_transaction_id(df, config.id_column)

    if args.seed_dirty:
        seeder = DirtyDataSeeder(random_state=config.random_state)
        dirty_df, labels_df = seeder.seed(df, dirty_rate=args.seed_rate)

        source.write(dirty_df, "seeded_dirty_data")
        source.write(labels_df, "seeded_dirty_labels")

        print("=== SEEDED DIRTY DATA GENERATED ===")
        print(f"Dirty data: {output_dir / 'seeded_dirty_data.csv'}")
        print(f"Labels: {output_dir / 'seeded_dirty_labels.csv'}")
        return

    ensure_columns_exist(df, list(config.rules.keys()))

    pipeline = DataCleaningPipelineService(config)
    issues_df = pipeline.run(df)

    report_service = ReportService()
    summary_df = report_service.build_summary(issues_df)
    recommendations_df = report_service.build_recommendations(issues_df)
    profile_df = report_service.build_dataset_profile(df, issues_df)

    source.write(issues_df, "detected_issues")
    source.write(recommendations_df, "recommendations")
    source.write(summary_df, "final_report")
    source.write(profile_df, "dataset_profile")

    if args.apply_fixes:
        fix_service = FixService(config)
        fixed_df = fix_service.apply_fixes(
            df=df,
            issues_df=issues_df,
            mode=args.mode,
        )
        source.write(fixed_df, "fixed_data")

    if args.report:
        print("=== REPORT ===")
        print(summary_df)
        print()
        print("=== DATASET PROFILE ===")
        print(profile_df.head(20))
        print()
        print("=== SAMPLE ISSUES ===")
        print(issues_df.head(20))

    print("=== PIPELINE COMPLETED ===")
    print(f"Total issues: {len(issues_df)}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()