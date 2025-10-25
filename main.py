from flask import Flask, Response, jsonify, request, send_file
import os
from dotenv import load_dotenv
import json
import requests
from flask_cors import CORS
from models import db, Country
from datetime import datetime, timezone
import random
from sqlalchemy import func, desc
import unicodedata
import pymysql
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
pymysql.install_as_MySQLdb()

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI")
if not app.config["SQLALCHEMY_DATABASE_URI"]:
    raise ValueError("SQLALCHEMY_DATABASE_URI environment variable is required")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
CORS(app)



with app.app_context():
    db.create_all()

def normalize_name(name):
    return unicodedata.normalize("NFKD", name)

@app.route("/")
def home():
    return "Welcome to the Country Currency & Exchange API"

@app.route("/countries/refresh", methods=["POST"])
def get_all_countries():
    COUNTRIES_API = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
    EXCHANGE_API = "https://open.er-api.com/v6/latest/USD"
    last_refresh = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        countries_response = requests.get(COUNTRIES_API, timeout=10)
        if countries_response.status_code != 200:
            return jsonify({
                "error": "External data source unavailable",
                "details": "Could not fetch data from Countries API"
            }), 503
        countries_data = countries_response.json()
    except requests.RequestException:
        return jsonify({
            "error": "External data source unavailable",
            "details": "Could not fetch data from Countries API"
        }), 503

    try:
        exchange_response = requests.get(EXCHANGE_API, timeout=10)
        if exchange_response.status_code != 200:
            return jsonify({
                "error": "External data source unavailable",
                "details": "Could not fetch data from Exchange Rates API"
            }), 503
        exchange_data = exchange_response.json()
    except requests.RequestException:
        return jsonify({
            "error": "External data source unavailable",
            "details": "Could not fetch data from Exchange Rates API"
        }), 503
    try:
        for country in countries_data:
            try:
                currency_code = country["currencies"][0]["code"]
                exchange_rate = exchange_data["rates"].get(currency_code.upper())
                if not exchange_rate:
                    exchange_rate = None
                    estimated_gdp = None
                else:
                    estimated_gdp = country["population"] * random.randint(1000, 2000) / exchange_rate
            except (KeyError, IndexError):
                currency_code = None
                exchange_rate = None
                estimated_gdp = 0

            normalized_name = normalize_name(country["name"]).lower()
            existing_country = db.session.execute(
                db.select(Country).where(func.lower(Country.name) == normalized_name)
            ).scalar_one_or_none()
            
            if existing_country:
                # Update existing
                existing_country.population = country["population"]
                existing_country.capital = country.get("capital")
                existing_country.region = country["region"]
                existing_country.currency_code = currency_code
                existing_country.exchange_rate = exchange_rate
                existing_country.estimated_gdp = estimated_gdp
                existing_country.flag_url = country["flag"]
                existing_country.last_refreshed_at = last_refresh
            else:
                # Insert new
                new_country = Country(
                    name=normalize_name(country["name"]),
                    population=country["population"],
                    capital=country.get("capital"),
                    region=country["region"],
                    currency_code=currency_code,
                    exchange_rate=exchange_rate,
                    estimated_gdp=estimated_gdp,
                    flag_url=country["flag"],
                    last_refreshed_at=last_refresh
                )
                db.session.add(new_country)
        
        db.session.commit()  # Commit once after processing all countries
        
        generate_summary_image()
        return jsonify({"message": "Countries refreshed successfully"}), 200
        
    except Exception:
        db.session.rollback()
        return jsonify({
            "error": "Internal server error",
        }), 500

def generate_summary_image():
    # Query total countries and top 5 by GDP
    total_countries_result = db.session.execute(db.select(func.count(Country.id))).scalar()
    total_countries = total_countries_result if total_countries_result is not None else 0
    
    top5_query = db.select(Country).order_by(desc(Country.estimated_gdp)).limit(5)
    top5_countries = db.session.execute(top5_query).scalars().all()
    top5_countries = [c.to_dict() for c in top5_countries]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.axis('off')  # No axes for text-based summary
    
    # Title
    ax.text(0.5, 0.95, 'Countries Summary Chart', ha='center', va='center', fontsize=16, fontweight='bold')
    
    # Total countries
    ax.text(0.5, 0.85, f'Total number of countries: {total_countries}', ha='center', va='center', fontsize=12)
    
    # Top 5 list
    ax.text(0.5, 0.75, 'Top 5 countries by estimated GDP:', ha='center', va='center', fontsize=12, fontweight='bold')
    y_pos = 0.65
    i = 1
    for country in top5_countries:
        gdp_value = country.get("estimated_gdp", 0)
        gdp_str = f'${gdp_value / 1e12:.2f} trillion' if gdp_value >= 1e12 else f'${gdp_value / 1e9:.2f} billion'
        ax.text(0.5, y_pos, f'{i}. {country["name"]}: {gdp_str}', ha='center', va='center', fontsize=10)
        y_pos -= 0.08
        i += 1 
    
    # Timestamp
    timestamp = top5_countries[0]["last_refreshed_at"] if top5_countries else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ax.text(0.5, 0.05, f'Last refresh: {timestamp}', ha='center', va='center', fontsize=10, style='italic')
    
    # Save to file
    os.makedirs('cache', exist_ok=True)
    image_path = 'cache/summary.png'
    plt.savefig(image_path, bbox_inches='tight', dpi=150, facecolor='white')
    plt.close(fig)
    
    print(f'Summary image saved to {image_path}')

@app.route("/countries/image", methods=["GET"])
def get_summary_image():
    image_path = 'cache/summary.png'
    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/png')
    else:
        return jsonify({"error": "Summary image not found"}), 404


@app.route("/status", methods=["GET"])
def get_status():
    total_countries_result = db.session.execute(db.select(func.count(Country.id))).scalar()
    total_countries = total_countries_result if total_countries_result is not None else 0
    
    last_refreshed_result = db.session.execute(
        db.select(Country.last_refreshed_at).order_by(Country.last_refreshed_at.desc()).limit(1)
    ).scalar()
    last_refreshed_at = last_refreshed_result if last_refreshed_result else None
    
    response = {
        "total_countries": total_countries,
        "last_refreshed_at": last_refreshed_at,
    }
    resposne_str = json.dumps(response, indent=2)
    return Response(resposne_str, mimetype="application/json"),200

@app.route("/countries", methods=["GET"])
def get_countries():
    if request.args.keys():
        allowed_params = {
            "region",
            "currency",
            "sort",
        }
        for param in request.args.keys():
            if param not in allowed_params:
                return jsonify({
                    "error": f"Validation failed: Invalid parameter '{param}'"
                }), 400
        
        region = request.args.get("region")
        currency = request.args.get("currency")
        sort = request.args.get("sort")
        
        try:
            # Start with base query
            query = db.select(Country)
            
            # Apply filters
            if region:
                query = query.filter(func.lower(Country.region) == region.lower())
            if currency:
                query = query.filter(func.lower(Country.currency_code) == currency.lower())
            
            # Apply sorting
            if sort == "gdp_desc":
                query = query.order_by(desc(Country.estimated_gdp))
            elif sort == "gdp_asc":
                query = query.order_by(Country.estimated_gdp)
            
            country_db = db.session.execute(query).scalars().all()
            countries = [c.to_dict() for c in country_db]
            if countries:
                countries_json = json.dumps(countries, indent=2)
                return Response(countries_json, mimetype="application/json"),200
            return jsonify(error="Country not found"), 404 
        except TypeError as e:
            return jsonify({
                    "error": f"Validation failed: {e} "
                }), 400
    
    country_db = db.session.execute(db.select(Country)).scalars().all()
    countries = [c.to_dict() for c in country_db]
    countries_json = json.dumps(countries, indent=2)
    return Response(countries_json, mimetype="application/json"),200


@app.route("/countries/<country_name>", methods=["GET", "DELETE"])
def specific_country(country_name):
    if request.method == "DELETE":
        country = db.session.execute(db.select(Country).where(func.lower(Country.name) == country_name.lower())).scalar_one_or_none()
        if country:
            db.session.delete(country)
            db.session.commit()
            return jsonify(message="Country deleted Successfully"), 200
        return jsonify(error="Country not found"), 404
    
    country = db.session.execute(db.select(Country).where(func.lower(Country.name) == country_name.lower())).scalar_one_or_none()
    if country:
        response = country.to_dict()
        response_str = json.dumps(response, indent=2)
        return Response(response_str, mimetype="application/json"), 200
    return jsonify(error="Country not found"), 404


if __name__ == "__main__":
    app.run(debug=True)