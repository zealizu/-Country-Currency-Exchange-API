# Country Currency & Exchange API

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A RESTful Flask API that fetches country data (name, capital, region, population, flag, currencies) from the [REST Countries API](https://restcountries.com/), exchange rates from [ExchangeRate-API](https://open.er-api.com/), and estimates GDP based on population and random per-capita income adjusted for exchange rates. Data is persisted in a MySQL database. Supports filtering, sorting, CRUD operations on countries, and generates a summary image (total countries, top 5 by estimated GDP, timestamp) on refresh.

## Features

- **Data Refresh**: Fetch and update country data from external APIs on demand.
- **CRUD Operations**: Read (list/filter/sort), get single, delete countries.
- **Query Parameters**: Filter by `region` (e.g., Africa), `currency` (e.g., USD), sort by `gdp_desc` or `gdp_asc`.
- **Summary Image**: Generates and serves a PNG summary chart after refresh.
- **Status Endpoint**: Quick overview of total countries and last refresh time.
- **CORS Enabled**: Suitable for web frontend integration.
- **Case-Insensitive Searches**: Normalized names and filters.
- **Error Handling**: Comprehensive validation, try-catch for DB/API failures.

## Tech Stack

- **Backend**: Flask, Flask-SQLAlchemy
- **Database**: MySQL (via PyMySQL)
- **External APIs**: REST Countries, ExchangeRate-API
- **Visualization**: Matplotlib (for summary image)
- **Other**: Requests, Flask-CORS, python-dotenv

## Installation

1. **Clone the Repository**:

   ```
   git clone <your-repo-url>
   cd country-currency-api
   ```

2. **Create Virtual Environment** (Recommended):

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:

   ```
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**:
   Create a `.env` file in the project root (add to `.gitignore`):

   ```
   SQLALCHEMY_DATABASE_URI=mysql+pymysql://user:password@host:port/dbname?ssl_ca=/path/to/ca.pem&ssl_mode=REQUIRED
   ```

   - Replace with your MySQL credentials (e.g., Aiven-hosted DB).
   - For SSL (Aiven), download `ca.pem` from Aiven Console and place in project root; update path to `/app/ca.pem` for deployment.

5. **Database Setup**:

   - Ensure your MySQL DB is running and accessible.
   - The app auto-creates tables on startup via `db.create_all()`.

6. **Run Locally**:
   ```
   python app.py
   ```
   - App runs on `http://localhost:5000` (debug mode).

## Usage

### API Endpoints

| Method   | Endpoint                    | Description                                                                | Parameters                                  | Response                                                                          |
| -------- | --------------------------- | -------------------------------------------------------------------------- | ------------------------------------------- | --------------------------------------------------------------------------------- |
| `GET`    | `/`                         | Welcome message                                                            | -                                           | `Welcome to the Country Currency & Exchange API`                                  |
| `POST`   | `/countries/refresh`        | Fetch/update all countries from APIs, estimate GDP, generate summary image | -                                           | `{"message": "Countries refreshed successfully"}`                                 |
| `GET`    | `/countries`                | List all or filtered/sorted countries                                      | `?region=Africa&currency=USD&sort=gdp_desc` | JSON array of countries                                                           |
| `GET`    | `/countries/<country_name>` | Get single country by name (case-insensitive)                              | `<country_name>` (e.g., united states)      | JSON object or `{"error": "Country not found"}`                                   |
| `DELETE` | `/countries/<country_name>` | Delete country by name                                                     | `<country_name>`                            | `{"message": "Country deleted successfully"}` or `{"error": "Country not found"}` |
| `GET`    | `/countries/image`          | Serve summary PNG image (total countries, top 5 GDP, timestamp)            | -                                           | PNG file or `{"error": "Summary image not found"}`                                |
| `GET`    | `/status`                   | API status (total countries, last refresh)                                 | -                                           | `{"total_countries": 195, "last_refreshed_at": "2025-10-25T11:57:12Z"}`           |

#### Example Requests

- Refresh Data:

  ```
  curl -X POST http://localhost:5000/countries/refresh
  ```

- List Filtered Countries:

  ```
  curl "http://localhost:5000/countries?region=Europe&sort=gdp_desc"
  ```

- Get Country:

  ```
  curl http://localhost:5000/countries/united%20states
  ```

- Delete Country:

  ```
  curl -X DELETE http://localhost:5000/countries/united%20states
  ```

- Serve Image:
  ```
  curl http://localhost:5000/countries/image --output summary.png
  ```

### Country Model (JSON Response Example)

```json
{
  "name": "United States",
  "capital": "Washington, D.C.",
  "region": "Americas",
  "population": 329484123,
  "currency_code": "USD",
  "exchange_rate": 1.0,
  "estimated_gdp": 21000000000000.0,
  "flag_url": "https://flagcdn.com/w320/us.png",
  "last_refreshed_at": "2025-10-25T11:57:12Z"
}
```

**Notes**:

- GDP is estimated (population × random $1K-$2K per capita / exchange rate).
- Filters: Exact match (case-insensitive). Empty results return `[]` (200 OK).
- Image: Generated on refresh; saved to `./cache/summary.png` (use Volumes for persistence).

## Deployment

### Railway (Recommended)

1. **Push to GitHub**: Commit code (exclude `.env`).
2. **Create Service**: In Railway dashboard, deploy from GitHub repo.
3. **Set Variables**:
   - `SQLALCHEMY_DATABASE_URI`: `mysql+pymysql://avnadmin:password@host:port/defaultdb?ssl_ca=/app/ca.pem&ssl_mode=REQUIRED`
   - Include `ca.pem` in repo root.
4. **Add Volume**: For persistent cache, mount to `/app/cache` (1GB recommended).
5. **Deploy**: Auto-builds with `requirements.txt`. Access via `https://your-app.railway.app`.

### Other Platforms

- **Heroku**: Use `Procfile`: `web: gunicorn app:app`. Add DB add-on (e.g., ClearDB MySQL).
- **Docker**: See `Dockerfile` example below.

#### Dockerfile (Optional)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

## Environment Variables

| Variable                  | Required | Description                                        | Default |
| ------------------------- | -------- | -------------------------------------------------- | ------- |
| `SQLALCHEMY_DATABASE_URI` | Yes      | MySQL connection string (e.g., Aiven URI with SSL) | None    |

## Contributing

1. Fork the repo.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Commit changes (`git commit -m 'Add amazing feature'`).
4. Push to branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

Pull requests welcome! Focus on bug fixes, new endpoints, or optimizations.
