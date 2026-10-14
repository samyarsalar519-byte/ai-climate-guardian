"""
AI Climate Guardian - Final Version
NASA Space Apps Challenge 2026
Challenge: "Be An Earth System Trend Detective!"

Scientific question: Is the warming trend the same across different US
climate zones, or are some regions changing faster - or even in the
opposite direction - than others?

Data source: NASA POWER (power.larc.nasa.gov)
- T2M: air temperature at 2 meters, from the MERRA-2 atmospheric
  reanalysis model (not a direct satellite sensor reading)
- Spatial resolution: ~0.5 degrees (~50 km); temporal resolution: daily

AI usage note: Claude (Anthropic) was used as a coding and learning
assistant. The team designed the scientific question, selected and
justified the four cities, found and fixed a data-quality bug (invalid
-999 values from NASA POWER), and interpreted the final results.
"""

import urllib.request
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

CITIES = {
    "Phoenix":  {"coords": (33.4484, -112.0740), "climate": "Hot desert"},
    "Seattle":  {"coords": (47.6062, -122.3321), "climate": "Temperate oceanic"},
    "Denver":   {"coords": (39.7392, -104.9903), "climate": "Cold semi-arid highland"},
    "Miami":    {"coords": (25.7617, -80.1918), "climate": "Humid subtropical"},
}
TREND_YEARS = 8


def fetch_nasa_data(lat, lon, start_str, end_str):
    url = ("https://power.larc.nasa.gov/api/temporal/daily/point"
        f"?parameters=T2M,RH2M&community=RE"
        f"&longitude={lon}&latitude={lat}"
        f"&start={start_str}&end={end_str}&format=JSON")
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read())
    return data["properties"]["parameter"]


def clean_and_validate(raw_dict, label=""):
    """Remove NASA POWER's missing-data marker (-999) before analysis."""
    all_values = list(raw_dict.values())
    clean = [v for v in all_values if v > -900]
    removed = len(all_values) - len(clean)
    if removed > 0:
        print("  [Validation -", label, "] Removed", removed, "invalid values.")
    return clean


def linear_trend_slope(years, values):
    """Least-squares slope: degrees C change per year."""
    n = len(years)
    mean_x = sum(years) / n
    mean_y = sum(values) / n
    num = sum((years[i] - mean_x) * (values[i] - mean_y) for i in range(n))
    den = sum((years[i] - mean_x) ** 2 for i in range(n))
    return num / den if den != 0 else 0


def get_city_warming_trend(lat, lon, years_back=TREND_YEARS):
    current_year = datetime.now().year
    years_list = []
    avg_temps = []
    for i in range(years_back):
        year = current_year - i
        try:
            raw = fetch_nasa_data(lat, lon, str(year) + "0701", str(year) + "0731")
            temps = clean_and_validate(raw["T2M"], label=str(year))
            if temps:
                years_list.append(year)
                avg_temps.append(sum(temps) / len(temps))
        except Exception:
            print("  Data for", year, "not available.")
    years_list.reverse()
    avg_temps.reverse()
    slope = linear_trend_slope(years_list, avg_temps)
    return years_list, avg_temps, slope


def interpret_slope(slope):
    if slope > 0.1:
        return "Fast, significant warming trend"
    elif slope > 0.03:
        return "Mild warming trend"
    elif slope > -0.03:
        return "No noticeable change"
    else:
        return "Cooling trend (needs further review)"


def get_priority_recommendation(rank, total_cities):
    if rank == 1:
        return "HIGH PRIORITY: fastest warming rate in our sample."
    elif rank <= total_cities / 2:
        return "MODERATE PRIORITY: warming above group median."
    else:
        return "LOWER RELATIVE PRIORITY within this sample."


if __name__ == "__main__":
    print("Checking warming trend for 4 US cities across different climate zones...")

    results = {}
    for city, info in CITIES.items():
        lat, lon = info["coords"]
        print("---", city, "---")
        years, temps, slope = get_city_warming_trend(lat, lon)
        results[city] = {
            "climate": info["climate"],
            "years": years,
            "temps": temps,
            "slope": slope,
            "verdict": interpret_slope(slope),
        }

    sorted_by_slope = sorted(results.items(), key=lambda x: x[1]["slope"], reverse=True)

    print("\nSCIENTIFIC CONCLUSION")
    fastest_city, fastest_info = sorted_by_slope[0]
    slowest_city, slowest_info = sorted_by_slope[-1]
    print("Fastest warming:", fastest_city, "-", round(fastest_info["slope"], 3), "C/year")
    print("Slowest warming:", slowest_city, "-", round(slowest_info["slope"], 3), "C/year")

    print("\nSUMMARY TABLE")
    total = len(sorted_by_slope)
    for rank, (city, info) in enumerate(sorted_by_slope, start=1):
        rec = get_priority_recommendation(rank, total)
        print(rank, city, "-", round(info["slope"], 3), "C/year")
        print("  ", info["verdict"])
        print("  ", rec)

    plt.figure(figsize=(9, 5))
    for city, info in results.items():
        plt.plot(info["years"], info["temps"], marker="o", label=city)
    plt.title("July Temperature Trend - 4 US Climate Zones")
    plt.xlabel("Year")
    plt.ylabel("Average Temperature (C)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()

    sorted_cities = sorted(results.items(), key=lambda x: x[1]["slope"], reverse=True)
    names = [pair[0] for pair in sorted_cities]
    slopes = [pair[1]["slope"] for pair in sorted_cities]

    plt.figure(figsize=(8, 4))
    plt.bar(names, slopes, color="orangered")
    plt.title("Annual Warming Rate by City")
    plt.ylabel("C per year")
    plt.show()
