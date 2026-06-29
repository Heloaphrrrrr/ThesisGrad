On Windows, `psql` may not be available in `PATH` even when PostgreSQL is installed.

Use the executable directly:

```bat
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d doantn
```

Or add this directory to `PATH`:

```text
C:\Program Files\PostgreSQL\18\bin
```
