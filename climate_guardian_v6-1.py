import urllib.request
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

CITIES = {
    "Tehran":       {"coords": (35.6892, 51.3890), "climate": "Semi-arid plateau"},
    "Ahvaz":        {"coords": (31.3183, 48.6706), "climate": "Hot desert"},
    "Bandar Abbas": {"coords": (27.1865, 56.2808), "climate": "Humid coastal"},
    "Tabriz":       {"coords": (38.0800, 46.2919), "climate": "Cool highland"},
}
TREND_YEARS = 8


def fetch_nasa_data(lat, lon, start_str, end_str):
    url = (
        "https://power.larc.nasa.gov/api/temporal/daily/point"
        f"?parameters=T2M,RH2M&community=RE"
        f"&longitude={lon}&latitude={lat}"
        f"&start={start_str}&end={end_str}&format=JSON"
    )
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read())
    return data["properties"]["parameter"]


def clean_and_validate(raw_dict, label=""):
    all_values = list(raw_dict.values())
    clean = [v for v in all_values if v > -900]
    removed = len(all_values) - len(clean)
    if removed > 0:
        print(f"  [Validation - {label}] Removed {removed} invalid values out of {len(all_values)}.")
    return clean


def linear_trend_slope(years, values):
    n = len(years)
    mean_x = sum(years) / n
    mean_y = sum(values) / n
    num = sum((years[i] - mean_x) * (values[i] - mean_y) for i in range(n))
    den = sum((years[i] - mean_x) ** 2 for i in range(n))
    return num / den if den != 0 else 0


def get_city_warming_trend(lat, lon, years_back=TREND_YEARS):
    current_year = datetime.now().year
    years_list, avg_temps = [], []
    for i in range(years_back):
        year = current_year - i
        try:
            raw = fetch_nasa_data(lat, lon, f"{year}0701", f"{year}0731")
            temps = clean_and_validate(raw["T2M"], label=f"{year}")
            if temps:
                years_list.append(year)
                avg_temps.append(sum(temps) / len(temps))
        except Exception:
            print(f"  Data for {year} not available.")
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
    """
    Soft, non-prescriptive recommendation layer based on relative
    warming-rate ranking. This is a decision-support suggestion,
    not a definitive policy directive.
    """
    if rank == 1:
        return ("HIGH PRIORITY: This city shows the fastest warming rate in our "
                "sample. It may benefit from closer monitoring and early "
                "consideration of heat-adaptation measures (e.g. passive building "
                "cooling, urban green space).")
    elif rank <= total_cities / 2:
        return ("MODERATE PRIORITY: Warming here is above the group median. "
                "Worth tracking alongside higher-priority areas.")
    else:
        return ("LOWER RELATIVE PRIORITY (within this sample): Warming is slower "
                "than other zones studied, though this does not mean no action "
                "is needed overall.")


print("=" * 60)
print("Checking warming trend for 4 cities across Iran's climate zones")
print("(Average July temperature, last", TREND_YEARS, "years)")
print("=" * 60)

results = {}
for city, info in CITIES.items():
    lat, lon = info["coords"]
    print(f"\n--- {city} ({info['climate']}) ---")
    years, temps, slope = get_city_warming_trend(lat, lon)
    results[city] = {
        "climate": info["climate"],
        "years": years,
        "temps": temps,
        "slope": slope,
        "verdict": interpret_slope(slope),
    }

sorted_by_slope = sorted(results.items(), key=lambda x: x[1]["slope"], reverse=True)

print("\n" + "#" * 60)
print("# Scientific Conclusion")
print("#" * 60)
fastest_city, fastest_info = sorted_by_slope[0]
slowest_city, slowest_info = sorted_by_slope[-1]

print(f"Fastest warming: {fastest_city} ({fastest_info['climate']}) "
      f"— {fastest_info['slope']:.3f} °C/year")
print(f"Slowest warming: {slowest_city} ({slowest_info['climate']}) "
      f"— {slowest_info['slope']:.3f} °C/year")

slope_range = fastest_info["slope"] - slowest_info["slope"]
if slope_range > 0.05:
    print(f"\nAnswer: Yes, warming patterns differ across Iran's climate zones.")
    print(f"Difference between fastest and slowest: {slope_range:.3f} °C/year.")
else:
    print(f"\nAnswer: In this {TREND_YEARS}-year sample, no clear difference was found between climate zones.")

print("\n" + "=" * 60)
print("Summary Table with Priority Recommendations")
print("=" * 60)
total = len(sorted_by_slope)
for rank, (city, info) in enumerate(sorted_by_slope, start=1):
    rec = get_priority_recommendation(rank, total)
    print(f"\n{rank}. {city} ({info['climate']}) — {info['slope']:.3f} °C/year")
    print(f"   {info['verdict']}")
    print(f"   {rec}")

plt.figure(figsize=(9, 5))
for city, info in results.items():
    plt.plot(info["years"], info["temps"], marker="o", label=f"{city} ({info['slope']:.3f}°C/yr)")
plt.title("July Temperature Trend Across 4 Iranian Climate Zones")
plt.xlabel("Year")
plt.ylabel("Average Temperature (°C)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()

plt.figure(figsize=(8, 4))
names = [c for c, _ in sorted_by_slope]
slopes = [info["slope"] for _, info in sorted_by_slope]
plt.bar(names, slopes, color="orangered")
plt.title("Annual Warming Rate by Climate Zone")
plt.ylabel("°C per year")
plt.show()
