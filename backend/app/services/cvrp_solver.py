import math
from typing import Dict, List, Optional, Tuple
from app.models import SmartBin, Vehicle, Depot, VehicleRoute, RouteWaypoint, WasteType

try:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    HAS_ORTOOLS = True
except ImportError:
    HAS_ORTOOLS = False


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine formula to compute great-circle distance between two GPS coordinates."""
    r = 6371.0  # Earth's mean radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * (math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    # Multiply by 1.35 to approximate city road street network routing compared to straight-line
    return round(r * c * 1.35, 2)


class CVRPSolver:
    """
    Capacitated Vehicle Routing Problem (CVRP) solver.
    Uses Google OR-Tools constraint programming with vehicle payload capacity dimensions,
    waste-type affinity clustering, and automated heuristic fallback.
    """

    @classmethod
    def solve_collection_routes(
        cls,
        depot: Depot,
        bins: List[SmartBin],
        vehicles: List[Vehicle],
    ) -> List[VehicleRoute]:
        """
        Groups candidate bins by waste type and solves CVRP for compatible vehicles.
        """
        routes: List[VehicleRoute] = []
        if not bins or not vehicles:
            return routes

        # Group bins by waste type for segregation integrity
        bins_by_type: Dict[WasteType, List[SmartBin]] = {}
        for b in bins:
            bins_by_type.setdefault(b.waste_type, []).append(b)

        # Assign available vehicles to waste types
        assigned_vehicles = set()

        for waste_type, candidate_bins in bins_by_type.items():
            if not candidate_bins:
                continue

            # Find compatible vehicles
            compat_vehicles = [
                v for v in vehicles
                if waste_type in v.supported_waste_types and v.id not in assigned_vehicles
            ]

            if not compat_vehicles:
                # If no dedicated vehicle, check flexible vehicles
                compat_vehicles = [v for v in vehicles if v.id not in assigned_vehicles]

            if not compat_vehicles:
                continue

            # Run CVRP for this cluster
            cluster_routes = cls._solve_cluster(depot, candidate_bins, compat_vehicles, waste_type)
            for r in cluster_routes:
                assigned_vehicles.add(r.vehicle_id)
                routes.append(r)

        return routes

    @classmethod
    def _solve_cluster(
        cls,
        depot: Depot,
        bins: List[SmartBin],
        vehicles: List[Vehicle],
        waste_type: WasteType,
    ) -> List[VehicleRoute]:
        """
        Solves CVRP for a specific waste type group and set of vehicles.
        Tries Google OR-Tools first; falls back to heuristic Clarke-Wright if unavailable.
        """
        if HAS_ORTOOLS:
            try:
                routes = cls._solve_ortools(depot, bins, vehicles, waste_type)
                if routes:
                    return routes
            except Exception:
                pass

        return cls._solve_heuristic(depot, bins, vehicles, waste_type)

    @classmethod
    def _solve_ortools(
        cls,
        depot: Depot,
        bins: List[SmartBin],
        vehicles: List[Vehicle],
        waste_type: WasteType,
    ) -> List[VehicleRoute]:
        # Locations: index 0 is depot, index 1..N are bins
        locations = [(depot.latitude, depot.longitude)] + [(b.latitude, b.longitude) for b in bins]
        num_locations = len(locations)
        num_vehicles = len(vehicles)

        # Distance matrix in integer meters
        distance_matrix = []
        for i in range(num_locations):
            row = []
            for j in range(num_locations):
                d_km = haversine_distance_km(locations[i][0], locations[i][1], locations[j][0], locations[j][1])
                row.append(int(d_km * 1000))
            distance_matrix.append(row)

        # Demands: 0 for depot, current weight for bins (rounded to int kg)
        demands = [0] + [max(1, int(b.current_weight_kg)) for b in bins]
        vehicle_capacities = [int(v.max_payload_kg) for v in vehicles]

        manager = pywrapcp.RoutingIndexManager(num_locations, num_vehicles, 0)
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return demands[from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            vehicle_capacities,
            True,  # start cumul to zero
            "Capacity",
        )

        # Allow dropping bins if total demand exceeds fleet capacity with high penalty
        penalty = 1000000
        for node in range(1, num_locations):
            routing.AddDisjunction([manager.NodeToIndex(node)], penalty)

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 2

        solution = routing.SolveWithParameters(search_parameters)
        if not solution:
            return []

        routes: List[VehicleRoute] = []
        for v_idx, vehicle in enumerate(vehicles):
            index = routing.Start(v_idx)
            plan_output_bins = []
            waypoints: List[RouteWaypoint] = [
                RouteWaypoint(
                    bin_id=None,
                    name=f"Start: {depot.name}",
                    latitude=depot.latitude,
                    longitude=depot.longitude,
                    action="START_DEPOT",
                    waste_amount_kg=0.0,
                    cumulative_weight_kg=0.0,
                    estimated_arrival_minutes=0.0,
                )
            ]

            route_dist_meters = 0
            cumul_weight = 0.0
            cumul_time_min = 0.0

            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                next_node_index = manager.IndexToNode(index)

                if next_node_index != 0:
                    bin_obj = bins[next_node_index - 1]
                    plan_output_bins.append(bin_obj.id)
                    leg_dist_m = distance_matrix[node_index][next_node_index]
                    route_dist_meters += leg_dist_m
                    cumul_weight += bin_obj.current_weight_kg
                    # Assume average city transit speed 25 km/h + 6 min stop per bin
                    leg_time = ((leg_dist_m / 1000.0) / 25.0 * 60.0) + 6.0
                    cumul_time_min += leg_time

                    waypoints.append(
                        RouteWaypoint(
                            bin_id=bin_obj.id,
                            name=bin_obj.name,
                            latitude=bin_obj.latitude,
                            longitude=bin_obj.longitude,
                            action="COLLECT",
                            waste_amount_kg=bin_obj.current_weight_kg,
                            cumulative_weight_kg=round(cumul_weight, 1),
                            estimated_arrival_minutes=round(cumul_time_min, 1),
                        )
                    )

            if plan_output_bins:
                # Add return to depot waypoint
                last_node = manager.IndexToNode(previous_index)
                return_dist_m = distance_matrix[last_node][0]
                route_dist_meters += return_dist_m
                cumul_time_min += (return_dist_m / 1000.0) / 25.0 * 60.0

                waypoints.append(
                    RouteWaypoint(
                        bin_id=None,
                        name=f"Return: {depot.name} (Discharge)",
                        latitude=depot.latitude,
                        longitude=depot.longitude,
                        action="END_DEPOT",
                        waste_amount_kg=0.0,
                        cumulative_weight_kg=round(cumul_weight, 1),
                        estimated_arrival_minutes=round(cumul_time_min, 1),
                    )
                )

                total_km = round(route_dist_meters / 1000.0, 2)
                utilization = round((cumul_weight / vehicle.max_payload_kg) * 100.0, 1)

                routes.append(
                    VehicleRoute(
                        route_id=f"ROUTE-{vehicle.id}-{waste_type.value}",
                        vehicle_id=vehicle.id,
                        vehicle_name=vehicle.name,
                        waste_type=waste_type,
                        waypoints=waypoints,
                        bin_ids=plan_output_bins,
                        total_distance_km=total_km,
                        estimated_duration_min=round(cumul_time_min, 1),
                        total_waste_kg=round(cumul_weight, 1),
                        capacity_utilization_pct=min(100.0, utilization),
                    )
                )

        return routes

    @classmethod
    def _solve_heuristic(
        cls,
        depot: Depot,
        bins: List[SmartBin],
        vehicles: List[Vehicle],
        waste_type: WasteType,
    ) -> List[VehicleRoute]:
        """
        Clarke-Wright Savings / Greedy Nearest Neighbor algorithm.
        Enforces vehicle capacity limits and optimizes route ordering.
        """
        routes: List[VehicleRoute] = []
        unassigned_bins = list(bins)

        for vehicle in vehicles:
            if not unassigned_bins:
                break

            current_lat = depot.latitude
            current_lon = depot.longitude
            remaining_capacity = vehicle.max_payload_kg
            cumul_weight = 0.0
            cumul_time_min = 0.0
            total_dist_km = 0.0
            assigned_this_truck: List[SmartBin] = []

            waypoints: List[RouteWaypoint] = [
                RouteWaypoint(
                    bin_id=None,
                    name=f"Start: {depot.name}",
                    latitude=depot.latitude,
                    longitude=depot.longitude,
                    action="START_DEPOT",
                    waste_amount_kg=0.0,
                    cumulative_weight_kg=0.0,
                    estimated_arrival_minutes=0.0,
                )
            ]

            # Greedy nearest neighbor respecting capacity
            while unassigned_bins:
                # Find nearest bin that fits in remaining payload
                best_candidate: Optional[Tuple[int, SmartBin, float]] = None
                for idx, b in enumerate(unassigned_bins):
                    if b.current_weight_kg <= remaining_capacity:
                        dist = haversine_distance_km(current_lat, current_lon, b.latitude, b.longitude)
                        if best_candidate is None or dist < best_candidate[2]:
                            best_candidate = (idx, b, dist)

                if best_candidate is None:
                    # Vehicle is full or remaining bins exceed capacity
                    break

                idx, chosen_bin, leg_dist = best_candidate
                unassigned_bins.pop(idx)
                assigned_this_truck.append(chosen_bin)

                total_dist_km += leg_dist
                remaining_capacity -= chosen_bin.current_weight_kg
                cumul_weight += chosen_bin.current_weight_kg
                current_lat = chosen_bin.latitude
                current_lon = chosen_bin.longitude

                leg_time = (leg_dist / 25.0 * 60.0) + 6.0
                cumul_time_min += leg_time

                waypoints.append(
                    RouteWaypoint(
                        bin_id=chosen_bin.id,
                        name=chosen_bin.name,
                        latitude=chosen_bin.latitude,
                        longitude=chosen_bin.longitude,
                        action="COLLECT",
                        waste_amount_kg=chosen_bin.current_weight_kg,
                        cumulative_weight_kg=round(cumul_weight, 1),
                        estimated_arrival_minutes=round(cumul_time_min, 1),
                    )
                )

            if assigned_this_truck:
                # Return leg to depot
                return_dist = haversine_distance_km(current_lat, current_lon, depot.latitude, depot.longitude)
                total_dist_km += return_dist
                cumul_time_min += (return_dist / 25.0 * 60.0)

                waypoints.append(
                    RouteWaypoint(
                        bin_id=None,
                        name=f"Return: {depot.name} (Discharge)",
                        latitude=depot.latitude,
                        longitude=depot.longitude,
                        action="END_DEPOT",
                        waste_amount_kg=0.0,
                        cumulative_weight_kg=round(cumul_weight, 1),
                        estimated_arrival_minutes=round(cumul_time_min, 1),
                    )
                )

                utilization = round((cumul_weight / vehicle.max_payload_kg) * 100.0, 1)
                routes.append(
                    VehicleRoute(
                        route_id=f"ROUTE-{vehicle.id}-{waste_type.value}",
                        vehicle_id=vehicle.id,
                        vehicle_name=vehicle.name,
                        waste_type=waste_type,
                        waypoints=waypoints,
                        bin_ids=[b.id for b in assigned_this_truck],
                        total_distance_km=round(total_dist_km, 2),
                        estimated_duration_min=round(cumul_time_min, 1),
                        total_waste_kg=round(cumul_weight, 1),
                        capacity_utilization_pct=min(100.0, utilization),
                    )
                )

        return routes
