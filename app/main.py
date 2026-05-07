from app.config import build_default_config
from app.data_access.csv_source import CSVDataSource
from app.services.pipeline_service import DataCleaningPipelineService
from app.services.report_service import ReportService
from app.utils import normalize_empty_strings, ensure_columns_exist


def main():
    # =========================
    # 1. CONFIG
    # =========================
    config = build_default_config()

    # =========================
    # 2. DATA SOURCE (CSV)
    # =========================
    source = CSVDataSource(
        input_path="data/employees_dirty.csv",
        output_dir="outputs",
    )

    # =========================
    # 3. LOAD DATA
    # =========================
    df = source.read()
    df = normalize_empty_strings(df)

    # kiểm tra cột
    ensure_columns_exist(df, list(config.rules.keys()))

    # =========================
    # 4. RUN PIPELINE
    # =========================
    pipeline = DataCleaningPipelineService(config)
    issues_df = pipeline.run(df)

    # =========================
    # 5. REPORT
    # =========================
    report_service = ReportService()

    summary_df = report_service.build_summary(issues_df)
    rec_df = report_service.build_recommendations(issues_df)

    # =========================
    # 6. SAVE OUTPUT
    # =========================
    source.write(issues_df, "detected_issues")
    source.write(rec_df, "recommendations")
    source.write(summary_df, "final_report")

    # =========================
    # 7. LOG
    # =========================
    print("=== PIPELINE COMPLETED ===")
    print(f"Total issues: {len(issues_df)}")
    print()
    print(summary_df)

    if not issues_df.empty:
        print("\nSample:")
        print(issues_df.head(10))


if __name__ == "__main__":
    main()