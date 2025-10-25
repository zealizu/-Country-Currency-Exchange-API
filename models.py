from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, Integer


class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Country(db.Model):
    id:Mapped[int] = mapped_column(Integer, primary_key=True)
    name:Mapped[str] = mapped_column(String(200), nullable=False)
    capital:Mapped[str] = mapped_column(String(200), nullable=True)
    region:Mapped[str] = mapped_column(String(200), nullable=True)
    population:Mapped[int] = mapped_column(Integer, nullable=False)
    currency_code:Mapped[str] = mapped_column(String(200), nullable=True)
    exchange_rate:Mapped[float] = mapped_column(Float, nullable=True)
    estimated_gdp:Mapped[float] = mapped_column(Float, nullable=True)
    flag_url: Mapped[str] = mapped_column(String(200), nullable=True)
    last_refreshed_at: Mapped[str] = mapped_column(String(200), nullable=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "capital": self.capital,
            "region": self.region,
            "population": self.population,
            "currency_code": self.currency_code,
            "exchange_rate": self.exchange_rate,
            "estimated_gdp": self.estimated_gdp,
            "flag_url": self.flag_url,
            "last_refreshed_at": self.last_refreshed_at
        }

    
    