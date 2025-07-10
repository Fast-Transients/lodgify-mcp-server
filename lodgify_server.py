#!/usr/bin/env python3
"""
Lodgify MCP Server

A Model Context Protocol server for interacting with the Lodgify vacation rental API.
Provides tools and resources for managing properties, bookings, rates, and calendar data.

Usage:
    uv add "mcp[cli]" httpx
    mcp install lodgify_server.py --name "Lodgify API" -v LODGIFY_API_KEY=your_api_key_here
"""

import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date
from typing import Any

import httpx
from mcp.server.fastmcp import Context, FastMCP  # type: ignore[import-not-found]
from mcp.server.fastmcp.prompts import base  # type: ignore[import-not-found]

# Constants
HTTP_OK = 200
PROPERTIES_SUMMARY_LIMIT = 10


@dataclass
class LodgifyConfig:
    """Configuration for Lodgify API access."""
    api_key: str
    base_url: str = "https://api.lodgify.com/v2"
    timeout: int = 30


@dataclass
class AppContext:
    """Application context with Lodgify client."""
    config: LodgifyConfig
    client: httpx.AsyncClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with Lodgify API client."""
    api_key = os.getenv("LODGIFY_API_KEY")
    if not api_key:
        raise ValueError("LODGIFY_API_KEY environment variable is required")

    config = LodgifyConfig(api_key=api_key)

    # Create HTTP client with proper headers
    client = httpx.AsyncClient(
        base_url=config.base_url,
        headers={
            "X-ApiKey": config.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        timeout=config.timeout
    )

    try:
        # Test API connection
        server.info("Testing Lodgify API connection...")  # type: ignore[attr-defined]
        response = await client.get("/properties", params={"limit": 1})
        if response.status_code == HTTP_OK:
            server.info("✅ Lodgify API connection successful")  # type: ignore[attr-defined]
        else:
            server.warning(f"⚠️ API test returned status {response.status_code}")  # type: ignore[attr-defined]

        yield AppContext(config=config, client=client)
    finally:
        await client.aclose()


# Create the MCP server
mcp = FastMCP(
    "Lodgify API Server",
    dependencies=["httpx>=0.25.0"],
    lifespan=app_lifespan
)


async def handle_api_error(response: httpx.Response) -> str:
    """Handle API errors and return user-friendly messages."""
    try:
        error_data = response.json()
        if isinstance(error_data, dict):
            message = error_data.get("message", f"API Error {response.status_code}")
            code = error_data.get("code", response.status_code)
            return f"Lodgify API Error {code}: {message}"
    except Exception:
        pass

    return f"HTTP {response.status_code}: {response.text[:200]}..."


# Global client reference - will be set during lifespan
_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    """Get the global HTTP client."""
    if _client is None:
        raise RuntimeError("Client not initialized")
    return _client


# Update the lifespan to set global client
@asynccontextmanager
async def app_lifespan_with_global(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with Lodgify API client."""
    global _client  # noqa: PLW0603

    api_key = os.getenv("LODGIFY_API_KEY")
    if not api_key:
        raise ValueError("LODGIFY_API_KEY environment variable is required")

    config = LodgifyConfig(api_key=api_key)

    # Create HTTP client with proper headers
    _client = httpx.AsyncClient(
        base_url=config.base_url,        headers={
            "X-ApiKey": config.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        timeout=config.timeout
    )

    try:
        # Test API connection
        print("Testing Lodgify API connection...", file=sys.stderr)
        response = await _client.get("/properties", params={"limit": 1})
        if response.status_code == HTTP_OK:
            print("Lodgify API connection successful", file=sys.stderr)
        else:
            print(f"API test returned status {response.status_code}", file=sys.stderr)

        yield AppContext(config=config, client=_client)
    finally:
        await _client.aclose()
        _client = None


# Recreate server with updated lifespan
mcp = FastMCP(
    "Lodgify API Server",
    dependencies=["httpx>=0.25.0"],
    lifespan=app_lifespan_with_global
)


# RESOURCES - Expose data for LLM context

@mcp.resource("lodgify://properties")
async def get_properties_list() -> str:
    """Get a summary list of all properties."""
    client = get_client()

    try:
        response = await client.get("/properties")
        response.raise_for_status()

        properties = response.json()
        if isinstance(properties, dict) and "items" in properties:
            properties_data = properties["items"]
        else:
            properties_data = properties

        # Format for LLM consumption
        summary = ["# Lodgify Properties Summary\n"]

        for prop in properties_data[:PROPERTIES_SUMMARY_LIMIT]:  # Limit to first 10 for overview
            summary.append(f"## Property ID: {prop.get('id', 'N/A')}")
            summary.append(f"- **Name**: {prop.get('name', 'N/A')}")
            summary.append(f"- **Type**: {prop.get('property_type', 'N/A')}")
            summary.append(f"- **Status**: {prop.get('status', 'N/A')}")
            summary.append(f"- **Max Guests**: {prop.get('max_guests', 'N/A')}")
            summary.append(f"- **Bedrooms**: {prop.get('bedrooms', 'N/A')}")
            summary.append("")

        if len(properties_data) > PROPERTIES_SUMMARY_LIMIT:
            summary.append(f"... and {len(properties_data) - PROPERTIES_SUMMARY_LIMIT} more properties.")

        return "\n".join(summary)

    except httpx.HTTPStatusError as e:
        return await handle_api_error(e.response)
    except Exception as e:
        return f"Error fetching properties: {str(e)}"


@mcp.resource("lodgify://property/{property_id}")
async def get_property_details(property_id: str) -> str:
    """Get detailed information about a specific property."""
    client = get_client()

    try:
        response = await client.get(f"/properties/{property_id}")
        response.raise_for_status()

        property_data = response.json()

        # Format property details for LLM
        details = [f"# Property Details: {property_data.get('name', 'N/A')}\n"]
        details.append(f"**Property ID**: {property_data.get('id', 'N/A')}")
        details.append(f"**Type**: {property_data.get('property_type', 'N/A')}")
        details.append(f"**Status**: {property_data.get('status', 'N/A')}")
        details.append(f"**Maximum Guests**: {property_data.get('max_guests', 'N/A')}")
        details.append(f"**Bedrooms**: {property_data.get('bedrooms', 'N/A')}")
        details.append(f"**Bathrooms**: {property_data.get('bathrooms', 'N/A')}")

        if property_data.get('description'):
            details.append(f"\n**Description**: {property_data['description']}")

        if property_data.get('address'):
            details.append(f"\n**Address**: {property_data['address']}")

        # Add room types if available
        if property_data.get('room_types'):
            details.append("\n## Room Types:")
            for room in property_data['room_types']:
                details.append(f"- **{room.get('name', 'N/A')}** (ID: {room.get('id', 'N/A')})")
                details.append(f"  - Max Guests: {room.get('max_guests', 'N/A')}")
                details.append(f"  - Base Rate: {room.get('base_rate', 'N/A')}")

        return "\n".join(details)

    except httpx.HTTPStatusError as e:
        return await handle_api_error(e.response)
    except Exception as e:
        return f"Error fetching property {property_id}: {str(e)}"


@mcp.resource("lodgify://bookings/recent")
async def get_recent_bookings() -> str:
    """Get recent bookings summary."""
    client = get_client()

    try:
        response = await client.get("/reservations/bookings", params={"size": 20})
        response.raise_for_status()

        bookings_data = response.json()
        if isinstance(bookings_data, dict) and "items" in bookings_data:
            bookings = bookings_data["items"]
        else:
            bookings = bookings_data

        summary = ["# Recent Bookings Summary\n"]

        for booking in bookings:
            summary.append(f"## Booking ID: {booking.get('id', 'N/A')}")
            summary.append(f"- **Guest**: {booking.get('guest_name', 'N/A')}")
            summary.append(f"- **Property**: {booking.get('property_name', booking.get('property_id', 'N/A'))}")
            summary.append(f"- **Arrival**: {booking.get('arrival', 'N/A')}")
            summary.append(f"- **Departure**: {booking.get('departure', 'N/A')}")
            summary.append(f"- **Status**: {booking.get('status', 'N/A')}")
            summary.append(f"- **Total**: {booking.get('total_amount', 'N/A')} {booking.get('currency_code', '')}")
            summary.append("")

        return "\n".join(summary)

    except httpx.HTTPStatusError as e:
        return await handle_api_error(e.response)
    except Exception as e:
        return f"Error fetching bookings: {str(e)}"


# TOOLS - Execute actions

@mcp.tool()
async def get_properties(
    ctx: Context,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None
) -> dict[str, Any]:
    """
    Get a list of properties with optional filtering.

    Args:
        limit: Maximum number of properties to return (default: 50)
        offset: Number of properties to skip (default: 0)
        status: Filter by property status (e.g., "Active", "Inactive")
    """
    client = get_client()

    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status

    try:
        response = await client.get("/properties", params=params)
        response.raise_for_status()

        return {
            "success": True,
            "data": response.json(),
            "message": f"Retrieved {limit} properties (offset: {offset})"
        }

    except httpx.HTTPStatusError as e:
        error_msg = await handle_api_error(e.response)
        return {"success": False, "error": error_msg}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_property_by_id(ctx: Context, property_id: int) -> dict[str, Any]:
    """
    Get detailed information about a specific property.

    Args:
        property_id: The unique ID of the property
    """
    client = get_client()

    try:
        response = await client.get(f"/properties/{property_id}")
        response.raise_for_status()

        return {
            "success": True,
            "data": response.json(),
            "message": f"Retrieved property {property_id}"
        }

    except httpx.HTTPStatusError as e:
        error_msg = await handle_api_error(e.response)
        return {"success": False, "error": error_msg}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_bookings(
    ctx: Context,
    size: int = 50,
    page: int = 1,
    property_id: int | None = None,
    status: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None
) -> dict[str, Any]:
    """
    Get bookings with optional filtering.

    Args:
        size: Maximum number of bookings to return
        page: Number of page to get
        property_id: Filter by specific property ID
        status: Filter by booking status (e.g., "Booked", "Cancelled")
        start_date: Filter bookings from this date (YYYY-MM-DD)
    end_date: Filter bookings until this date (YYYY-MM-DD)
    """
    client = get_client()

    params: dict[str, Any] = {"size": size, "page": page }
    if property_id:
        params["property_id"] = property_id
    if status:
        params["status"] = status
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    try:
        response = await client.get("/reservations/bookings", params=params)
        response.raise_for_status()

        return {
            "success": True,
            "data": response.json(),
            "message": f"Retrieved bookings with filters: {params}"
        }

    except httpx.HTTPStatusError as e:
        error_msg = await handle_api_error(e.response)
        return {"success": False, "error": error_msg}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def create_booking(
    ctx: Context,
    property_id: int,
    room_type_id: int,
    arrival: str,
    departure: str,
    guest_name: str,
    guest_email: str,
    guest_phone: str,
    guest_country_code: str,
    people: int = 2,
    total: float = 0.0,
    currency_code: str = "USD",
    status: str = "Booked",
    source_text: str = "MCP API"
) -> dict[str, Any]:
    """
    Create a new booking.

    Args:
        property_id: The property ID for the booking
        room_type_id: The room type ID within the property
        arrival: Arrival date (YYYY-MM-DD)
        departure: Departure date (YYYY-MM-DD)
        guest_name: Guest's full name
        guest_email: Guest's email address
        guest_phone: Guest's phone number
        guest_country_code: Guest's country code (e.g., "US", "CA")
        people: Number of people (default: 2)
        total: Total booking amount (default: 0.0)
        currency_code: Currency code (default: "USD")
        status: Booking status (default: "Booked")
        source_text: Source description (default: "MCP API")
    """
    client = get_client()

    booking_data = {
        "guest": {
            "name": guest_name,
            "email": guest_email,
            "phone": guest_phone,
            "country_code": guest_country_code
        },
        "status": status,
        "property_id": property_id,
        "arrival": arrival,
        "departure": departure,
        "bookability": "InstantBooking",
        "origin": "manual",
        "total": total,
        "currency_code": currency_code,
        "source_text": source_text,
        "rooms": [
            {
                "room_type_id": room_type_id,
                "people": people,
                "key_code": ""
            }
        ]
    }

    try:
        response = await client.post("/reservation/booking", json=booking_data)
        response.raise_for_status()

        return {
            "success": True,
            "data": response.json(),
            "message": f"Created booking for {guest_name} at property {property_id}"
        }

    except httpx.HTTPStatusError as e:
        error_msg = await handle_api_error(e.response)
        return {"success": False, "error": error_msg}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_calendar(
    ctx: Context,
    property_id: int,
    room_type_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None
) -> dict[str, Any]:
    """
    Get calendar/availability information for a property.

    Args:
        property_id: The property ID
        room_type_id: Optional room type ID within the property
        start_date: Start date for calendar (YYYY-MM-DD)
        end_date: End date for calendar (YYYY-MM-DD)
    """
    client = get_client()

    params: dict[str, Any] = {"HouseId": property_id}
    if room_type_id:
        params["RoomTypeId"] = room_type_id
    if start_date:
        params["StartDate"] = start_date
    if end_date:
        params["EndDate"] = end_date

    try:
        response = await client.get("/rates/calendar", params=params)
        response.raise_for_status()

        return {
            "success": True,
            "data": response.json(),
            "message": f"Retrieved calendar for property {property_id}"
        }

    except httpx.HTTPStatusError as e:
        error_msg = await handle_api_error(e.response)
        return {"success": False, "error": error_msg}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_booking_by_id(ctx: Context, booking_id: int) -> dict[str, Any]:
    """
    Get detailed information about a specific booking.

    Args:
        booking_id: The unique ID of the booking
    """
    client = get_client()

    try:
        response = await client.get(f"/reservations/bookings/{booking_id}")
        response.raise_for_status()

        return {
            "success": True,
            "data": response.json(),
            "message": f"Retrieved booking {booking_id}"
        }

    except httpx.HTTPStatusError as e:
        error_msg = await handle_api_error(e.response)
        return {"success": False, "error": error_msg}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def update_booking_status(
    ctx: Context,
    booking_id: int,
    status: str
) -> dict[str, Any]:
    """
    Update the status of an existing booking.

    Args:
        booking_id: The unique ID of the booking
        status: New status (e.g., "Booked", "Cancelled", "CheckedIn", "CheckedOut")
    """
    client = get_client()

    try:
        # First get the current booking data
        get_response = await client.get(f"/reservations/bookings/{booking_id}")
        get_response.raise_for_status()
        booking_data = get_response.json()

        # Update only the status
        booking_data["status"] = status

        # Send the update
        response = await client.put(f"/reservations/bookings/{booking_id}", json=booking_data)
        response.raise_for_status()

        return {
            "success": True,
            "data": response.json(),
            "message": f"Updated booking {booking_id} status to {status}"
        }

    except httpx.HTTPStatusError as e:
        error_msg = await handle_api_error(e.response)
        return {"success": False, "error": error_msg}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_occupancy_summary(
    ctx: Context,
    property_id: int,
    start_date: str,
    end_date: str
) -> dict[str, Any]:
    """
    Get occupancy summary, average rental rate, and total revenue for a property
    within a specified date range.

    Args:
        property_id: The property ID
        start_date: Start date for analysis (YYYY-MM-DD)
        end_date: End date for analysis (YYYY-MM-DD)
    """
    try:
        # Fetch calendar data
        calendar_response = await get_calendar(
            ctx,
            property_id=property_id,
            start_date=start_date,
            end_date=end_date
        )

        if not calendar_response["success"]:
            return {"success": False, "error": f"Failed to retrieve calendar data: {calendar_response['error']}"}

        calendar_data = calendar_response["data"]
        if not calendar_data:
            return {"success": True, "data": {}, "message": "No calendar data found for the specified period."}

        total_days = 0
        occupied_days = 0
        total_revenue = 0.0
        total_available_rate = 0.0
        available_days_with_rate = 0

        # Parse dates
        try:
            s_date = date.fromisoformat(start_date)
            e_date = date.fromisoformat(end_date)
        except ValueError as e:
            return {"success": False, "error": f"Invalid date format: {e}"}

        # Iterate through each day in the calendar data
        for day_data in calendar_data:
            try:
                day = date.fromisoformat(day_data["date"])
            except ValueError as e:
                return {"success": False, "error": f"Invalid date format in calendar data: {e}"}
            if s_date <= day <= e_date:
                total_days += 1
                if day_data.get("status") == "Booked":
                    occupied_days += 1
                    total_revenue += day_data.get("price", 0.0)
                elif day_data.get("status") == "Available" and day_data.get("price") is not None:
                    total_available_rate += day_data["price"]
                    available_days_with_rate += 1

        occupancy_rate = (occupied_days / total_days) * 100 if total_days > 0 else 0
        average_rental_rate = (total_revenue + total_available_rate) / (occupied_days + available_days_with_rate) if (occupied_days + available_days_with_rate) > 0 else 0

        summary = {
            "property_id": property_id,
            "start_date": start_date,
            "end_date": end_date,
            "total_days_in_period": total_days,
            "occupied_days": occupied_days,
            "occupancy_rate": f"{occupancy_rate:.2f}%",
            "total_revenue": f"{total_revenue:.2f}",
            "average_rental_rate": f"{average_rental_rate:.2f}"
        }

        return {
            "success": True,
            "data": summary,
            "message": "Occupancy summary generated successfully."
        }

    except httpx.HTTPStatusError as e:
        error_msg = await handle_api_error(e.response)
        return {"success": False, "error": error_msg}
    except Exception as e:
        return {"success": False, "error": str(e)}


# PROMPTS - Interactive templates

@mcp.prompt()
def analyze_lodgify_data() -> list[base.Message]:
    """Analyze Lodgify property and booking data for insights."""
    return [
        base.UserMessage(
            "I'd like to analyze my Lodgify data. Please help me understand:\n"
            "1. Property performance and occupancy rates\n"
            "2. Booking trends and patterns\n"
            "3. Revenue optimization opportunities\n"
            "4. Guest demographics and preferences\n\n"
            "Use the available Lodgify tools to gather current data and provide insights."
        )
    ]


@mcp.prompt()
def analyze_occupancy_data_prompt() -> list[base.Message]:
    """
    Analyze occupancy data for a specific property and date range.
    """
    return [
        base.UserMessage(
            "I want to analyze occupancy data for a property. Please provide the property ID, start date (YYYY-MM-DD), and end date (YYYY-MM-DD)."
        )
    ]


@mcp.prompt()
def create_booking_workflow() -> list[base.Message]:
    """Guide through creating a new booking in Lodgify."""
    return [
        base.UserMessage(
            "I need to create a new booking in Lodgify. Please guide me through:\n"
            "1. First, show me available properties\n"
            "2. Help me select the right property and room type\n"
            "3. Check availability for my desired dates\n"
            "4. Collect guest information and create the booking\n\n"
            "Let's start by getting the list of available properties."
        )
    ]


@mcp.prompt()
def property_management_review() -> list[base.Message]:
    """Review property management and booking status."""
    return [
        base.UserMessage(
            "Please provide a comprehensive review of my Lodgify account:\n"
            "1. Overview of all properties and their current status\n"
            "2. Recent bookings and their details\n"
            "3. Any upcoming check-ins or check-outs\n"
            "4. Properties that might need attention\n\n"
            "Use the Lodgify resources and tools to gather this information."
        )
    ]


def main() -> None:
    """Run the Lodgify MCP server."""
    mcp.run()
if __name__ == "__main__":
    main()
