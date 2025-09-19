# Integrating tools with Model Context Protocol (MCP)

In this section, we'll explore how to integrate Model Context Protocol (MCP) with our voice AI agent. MCP standardizes how applications provide context to LLMs, creating a consistent interface for integrating external tools and services with our voice agent.

## Understanding MCP

Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to Large Language Models (LLMs). It enables communication between the system and locally running MCP servers that provide additional tools and resources.

Learn More About MCP

To learn more about Model Context Protocol and available MCP servers, visit the [MCP documentation](https://modelcontextprotocol.io/docs/concepts/transports)  and explore the [AWS MCP Servers](https://awslabs.github.io/mcp/) .

## Example: AWS Location Service MCP server

For this example, we'll integrate the AWS Location Service MCP server, which provides geospatial capabilities to our voice AI agent. This allows our health assistant to provide location-aware information, such as finding nearby healthcare facilities.

AWS MCP Servers

AWS provides [several MCP servers](https://awslabs.github.io/mcp/)  that can be integrated with your applications and development workflow.

## Available AWS Location Service MCP Tools

The AWS Location Service MCP server provides [several tools](https://awslabs.github.io/mcp/servers/aws-location-mcp-server/)  that your voice AI agent can use:

1. **search_places**: Search for places using geocoding
    
    ```python
    search_places(query: str, max_results: int = 5, mode: str = 'summary')
    ```
    
2. **get_place**: Get details for a specific place by PlaceId
    
    ```python
    get_place(place_id: str, mode: str = 'summary')
    ```
    
3. **reverse_geocode**: Convert coordinates to addresses
    
    ```python
    reverse_geocode(longitude: float, latitude: float)
    ```
    
4. **search_nearby**: Search for places near a specified location
    
    ```python
    search_nearby(longitude: float, latitude: float, radius: int = 500, max_results: int = 5,
                 query: str = None, max_radius: int = 10000, expansion_factor: float = 2.0,
                 mode: str = 'summary')
    ```
    
5. **search_places_open_now**: Search for places that are currently open
    
    ```python
    search_places_open_now(query: str, max_results: int = 5, initial_radius: int = 500,
                          max_radius: int = 50000, expansion_factor: float = 2.0)
    ```
    
6. **calculate_route**: Calculate routes between locations
    
    ```python
    calculate_route(
        departure_position: list,  # [longitude, latitude]
        destination_position: list,  # [longitude, latitude]
        travel_mode: str = 'Car',  # 'Car', 'Truck', 'Walking', or 'Bicycle'
        optimize_for: str = 'FastestRoute'  # 'FastestRoute' or 'ShortestRoute'
    )
    ```
    
7. **get_coordinates**: Get coordinates for a location name or address
    
    ```python
    get_coordinates(location: str)
    ```
    
8. **optimize_waypoints**: Optimize the order of waypoints for a route
    
    ```python
    optimize_waypoints(
        origin_position: list,  # [longitude, latitude]
        destination_position: list,  # [longitude, latitude]
        waypoints: list,  # List of waypoints, each as a dict with at least Position [longitude, latitude]
        travel_mode: str = 'Car',
        mode: str = 'summary'
    )
    ```
    

## Integrating your MCP server with your voice AI agent using Strands

While Pipecat has [direct support for MCP](https://docs.pipecat.ai/server/base-classes/mcp/mcp)  for tool calls, you will integrate MCP using [Strands](https://strandsagents.com/) , an open source agentic framework. As you will see later, "agents as tools" allows for more dynamic conversations. Continue next to learn more!
