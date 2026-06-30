import sys

from app.cli import main


if __name__ == "__main__":
    sys.argv = [
        "run_pipeline_full.py",
        "--source",
        "postgres",
        "--connection-uri",
        "postgresql://postgres:Triweio_123@localhost:5432/doantn",
        "--config",
        "configs/ecommerce_config.yaml",
        "--apply-fixes",
    ]
    main()
