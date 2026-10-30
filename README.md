# Weather Data Engineering Pipeline

An end-to-end data engineering project that collects historical weather data from the Open-Meteo API, cleans and validates it using Python and Pandas, loads it into PostgreSQL, and transforms it using dbt.

The project supports both **local execution** and **Docker-based deployment**.

## Project Overview

This pipeline automates the collection, cleaning, storage, and transformation of historical weather observations for selected cities.

### Cities Covered
- Champaign, USA
- Chicago, USA
- New York, USA

### Data Period
October 1, 2025 – October 7, 2025

### Data Source
[Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)

## Architecture

```text
Open-Meteo Historical Weather API
              |
              v
       Data Ingestion
        (Python)
              |
              v
        Raw JSON Data
         data/raw/
              |
              v
      Data Cleaning
        (Pandas)
              |
              v
       Cleaned CSV
      data/processed/
              |
              v
       PostgreSQL
              |
              v
        dbt Models
              |
              v
       Analytics Layer
```

## Technologies Used

| Technology | Purpose |
|---|---|
| Python 3.12 | Pipeline development |
| Pandas | Data cleaning and transformation |
| Requests | API ingestion |
| PostgreSQL | Relational data storage |
| SQLAlchemy | Database connectivity |
| dbt | Data transformation and testing |
| Docker | Application containerization |
| Docker Compose | Multi-container orchestration |
| Pytest | Automated testing |
| Git & GitHub | Version control |

## Project Structure

```text
weather-data-pipeline/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── init/
│   └── 01_schema.sql
│
├── logs/
│
├── src/
│   ├── main.py
│   ├── clean_weather.py
│   ├── load_weather.py
│   └── update_wind_speed.py
│
├── tests/
│   ├── test_ingestion.py
│   ├── test_load_weather.py
│   └── test_weather_pipeline.py
│
├── weather_dbt/
│   ├── models/
│   └── dbt_project.yml
│
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Features

- Retrieves historical weather data using the Open-Meteo API.
- Stores raw API responses as JSON files.
- Validates API responses before processing.
- Cleans and standardizes weather measurements using Pandas.
- Handles missing values, invalid measurements, and duplicate records.
- Loads city and observation records into PostgreSQL.
- Uses database constraints to prevent duplicate observations.
- Maintains pipeline execution logs.
- Transforms raw database tables into analytical models using dbt.
- Includes automated tests using Pytest.
- Supports Docker-based deployment with PostgreSQL.

## Database Schema

### 1. cities

Stores information about the cities being monitored.

| Column | Description |
|---|---|
| city_id | Primary key |
| name | City name |
| country | Country |
| latitude | Geographic latitude |
| longitude | Geographic longitude |

### 2. weather_observations

Stores daily weather observations.

| Column | Description |
|---|---|
| observation_id | Primary key |
| city_id | Foreign key referencing cities |
| observation_timestamp | Observation date |
| temperature_c | Temperature in Celsius |
| precipitation_mm | Precipitation in millimeters |
| wind_speed_kmh | Wind speed in kilometers per hour |

**Note:** The pipeline calculates `temperature_c` as the midpoint of daily maximum and minimum temperatures because the source data does not provide a daily mean temperature in the selected fields. This is an estimate, not an observed daily average.

## Getting Started — Local Setup

### Prerequisites

- Python 3.12+
- PostgreSQL
- Git

### 1. Clone the repository

```bash
git clone https://github.com/alisharawat56/weather-data-pipeline.git

cd weather-data-pipeline
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create a PostgreSQL database named:

```sql
CREATE DATABASE weather_db;
```

Create the required tables using the schema in `init/01_schema.sql`, or use your existing database schema.

### 5. Configure environment variables

Create a `.env` file in the project root.

Example:

```env
PGHOST=127.0.0.1
PGPORT=5432
PGDATABASE=weather_db
PGUSER=postgres
PGPASSWORD=your_local_password
```

Replace the password with your actual PostgreSQL password.

### 6. Run the pipeline

```bash
python src/main.py
```

The pipeline will:
1. Fetch historical weather data.
2. Save raw API responses.
3. Clean and validate the data.
4. Load records into PostgreSQL.
5. Update missing wind-speed values where applicable.
6. Log pipeline execution details.

## Docker Setup

Docker Compose allows the application and PostgreSQL database to run in separate containers.

### Prerequisites

- Docker Desktop
- WSL 2 enabled on Windows
- Docker Compose

### 1. Configure environment variables

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and configure your password:

```env
POSTGRES_PASSWORD=your_strong_local_password
```

Keep `.env` private. Never commit it to GitHub.

### 2. Build and start the containers

From the project root:

```bash
docker compose up --build
```

This command:
- Builds the Python application image.
- Downloads the PostgreSQL image if needed.
- Creates the PostgreSQL database container.
- Waits for the database health check.
- Runs the weather pipeline.

### 3. Verify containers

```bash
docker compose ps -a
```

Expected status after a successful one-time pipeline run:

- `weather_postgres` — running and healthy.
- `weather_pipeline` — exited with code `0`.

An exit code of `0` indicates successful execution.

### 4. View application logs

```bash
docker compose logs app
```

Follow logs in real time:

```bash
docker compose logs -f app
```

### 5. Access PostgreSQL inside Docker

```bash
docker exec -it weather_postgres psql -U postgres -d weather_db
```

List tables:

```sql
\dt
```

Check observation count:

```sql
SELECT COUNT(*) FROM weather_observations;
```

Exit PostgreSQL:

```sql
\q
```

### 6. Stop containers

```bash
docker compose down
```

This stops and removes the containers but preserves the PostgreSQL data volume.

To remove the database volume and its data as well:

```bash
docker compose down -v
```

**Warning:** The second command permanently deletes the Docker-managed PostgreSQL data volume.

## dbt Transformations

The project uses dbt to transform PostgreSQL data into analytical models.

### Models

**stg_weather_observations**

A staging model that prepares weather observation data for analysis.

**daily_city_weather**

An analytical model that summarizes daily weather information by city.

### Run dbt

Activate your Python environment and navigate to the dbt project directory:

```powershell
cd weather_dbt
```

Run the models:

```bash
dbt run
```

Run data tests:

```bash
dbt test
```

Generate documentation:

```bash
dbt docs generate
dbt docs serve
```

Make sure your dbt profile is configured in `~/.dbt/profiles.yml` and that its database connection settings match your PostgreSQL environment.

For local execution, use `127.0.0.1` as the database host. For execution from another container on the same Compose network, use the database service hostname `db`.

## Testing

The project includes automated tests using Pytest.

Run all tests:

```bash
pytest -v
```

The test suite covers:
- API response validation.
- Weather data cleaning.
- Database loading behavior.
- Duplicate prevention.
- Pipeline execution logic.

## Logging

Pipeline execution logs are stored in:

```text
logs/pipeline.log
```

Logs capture pipeline progress, successful execution, and errors encountered during processing.

## Data Quality and Reliability

The pipeline incorporates several data quality measures:

- API response structure validation.
- Required field validation.
- Numeric data conversion.
- Missing-value handling.
- Physical range validation.
- Duplicate observation prevention.
- Database constraints.
- Automated unit and integration tests.

## Future Enhancements

Potential improvements include:

- Automating scheduled pipeline execution.
- Adding Apache Airflow for workflow orchestration.
- Implementing cloud storage using AWS S3.
- Adding a data warehouse layer.
- Building interactive weather dashboards using Power BI or Tableau.
- Expanding the pipeline to support more cities and longer date ranges.
- Adding monitoring and alerting for failed pipeline executions.

## Author

**Alisha Rawat**

Master's Student — Information Management  
University of Illinois Urbana-Champaign

## License

This project is intended for educational and portfolio purposes.