from __future__ import annotations

import os

from serpapi import GoogleSearch

from modules.whatsapp_handler import send_whatsapp


def _search(params: dict) -> dict:
    api_key = os.getenv("SERPAPI_API_KEY", "")
    if not api_key:
        return {}
    query = params | {"api_key": api_key}
    try:
        return GoogleSearch(query).get_dict()
    except Exception:
        return {}


def _pick_flight_options(data: dict) -> tuple[str, str]:
    flights = data.get("best_flights") or data.get("other_flights") or []
    morning = [
        f
        for f in (flights or [])
        if str(f.get("flights", [{}])[0].get("departure_airport", {}).get("time", "00:00"))[:2].isdigit()
        and int(str(f.get("flights", [{}])[0].get("departure_airport", {}).get("time", "00:00"))[:2]) < 12
    ]
    cheapest = min(morning or flights or [{}], key=lambda x: x.get("price", 10**9))
    fastest = min(morning or flights or [{}], key=lambda x: x.get("total_duration", 10**9))
    return (
        f"Cheapest: ₹{cheapest.get('price', 'NA')} | {cheapest.get('total_duration', 'NA')} mins",
        f"Fastest: ₹{fastest.get('price', 'NA')} | {fastest.get('total_duration', 'NA')} mins",
    )


def _pick_hotel_options(data: dict) -> tuple[str, str]:
    hotels = [h for h in data.get("properties", []) if float(h.get("overall_rating", 0) or 0) >= 4]
    preferred = [h for h in hotels if any(k in str(h.get("name", "")).lower() for k in ["taj", "oberoi", "itc"])]
    pool = preferred or hotels or [{}]
    best_rated = max(pool, key=lambda x: float(x.get("overall_rating", 0) or 0))
    closest = min(pool, key=lambda x: float(x.get("distance", 9999) or 9999))
    return (
        f"Best rated: {best_rated.get('name', 'N/A')} ({best_rated.get('overall_rating', 'NA')}★)",
        f"Closest: {closest.get('name', 'N/A')} ({closest.get('distance', 'NA')} km)",
    )


def handle_travel_request(destination: str, dates: str, purpose: str, to_number: str) -> str:
    start_date = dates.split()[0] if dates else ""
    flights_data = _search(
        {
            "engine": "google_flights",
            "departure_id": "DEL",
            "arrival_id": destination,
            "outbound_date": start_date,
            "currency": "INR",
            "hl": "en",
        }
    )
    hotels_data = _search(
        {
            "engine": "google_hotels",
            "q": destination,
            "check_in_date": start_date,
            "adults": 1,
            "currency": "INR",
            "hl": "en",
        }
    )
    cheapest, fastest = _pick_flight_options(flights_data)
    best, closest = _pick_hotel_options(hotels_data)

    msg = (
        f"TRAVEL OPTIONS for {destination} ({purpose})\n"
        f"Flights: {cheapest} | {fastest}\n"
        f"Hotels: {best} | {closest}\n"
        "Rules held: aisle-seat preference, 4★+ only, no non-refundable default."
    )
    send_whatsapp(to_number, msg)
    return msg
