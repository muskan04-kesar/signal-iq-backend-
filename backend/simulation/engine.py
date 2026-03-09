import random
import time
import math
from typing import Dict, List, Optional
from .models import (
    Intersection, IntersectionMode, SignalState, Vehicle, GridState, SignalUpdate, 
    EmergencyVehicle, AIStatus, AIPrediction, AIRecommendation,
    RoadOverview, ZoneOverview, GridOverview, IntersectionSummary, SignalDetails,
    TrafficPattern, PatternUpdateResult, OptimizationResult
)
from . import config
from .topology import CIVIL_LINES_SIGNALS, CIVIL_LINES_EDGES, topology_signals, adjacency

class SimulationEngine:
    def __init__(self):
        self.intersections: Dict[str, Intersection] = {}
        self.vehicles: List[Vehicle] = []
        self.emergency_vehicle: Optional[EmergencyVehicle] = None
        self.ai_status: Optional[AIStatus] = None
        self._last_ai_update = 0.0
        self.ai_mode = False # Global AI mode state
        self._initialize_grid()
        self._initialize_vehicles()

    def _get_edge_distance(self, source: str, target: str) -> float:
        for adj in adjacency.get(source, []):
            if adj["target"] == target:
                return adj["distance"]
        return 100.0

    def _get_vehicles_on_edge(self, source_id: str, target_id: str) -> List[Vehicle]:
        return [v for v in self.vehicles if v.edge_source == source_id and v.edge_target == target_id]

    def _initialize_grid(self):
        for sig in CIVIL_LINES_SIGNALS:
            intersection_id = sig["id"]
            start_ns = random.choice([SignalState.GREEN, SignalState.RED])
            start_ew = SignalState.RED if start_ns == SignalState.GREEN else SignalState.GREEN
            
            self.intersections[intersection_id] = Intersection(
                id=intersection_id,
                lat=sig["lat"],
                lng=sig["lng"],
                nsSignal=start_ns,
                ewSignal=start_ew,
                timer=random.randint(5, 10),
                mode=IntersectionMode.FIXED,
                nsGreenTime=config.MIN_GREEN_TIME,
                ewGreenTime=config.MIN_GREEN_TIME
            )

    def _initialize_vehicles(self):
        for i in range(20):
            self._spawn_vehicle()

    def _spawn_vehicle(self):
        if len(self.vehicles) >= config.MAX_VEHICLES:
            return

        edge = random.choice(CIVIL_LINES_EDGES)
        is_reverse = random.choice([True, False])
        if is_reverse:
            source = edge["target"]
            target = edge["source"]
        else:
            source = edge["source"]
            target = edge["target"]

        vehicle = Vehicle(
            id=f"v-{int(time.time() * 1000)}-{random.randint(100,999)}",
            edge_source=source,
            edge_target=target,
            position=random.uniform(0, 50), 
            speed=random.uniform(config.MIN_SPEED, config.MAX_SPEED),
            target_speed=random.uniform(config.MIN_SPEED, config.MAX_SPEED),
            type="car"
        )
        self.vehicles.append(vehicle)

    def update(self, dt: float):
        self._update_signals(dt)
        self._update_vehicles(dt)
        if self.emergency_vehicle is not None and self.emergency_vehicle.active:
            self._update_emergency_vehicle(dt)
        
        self._run_ai_decision_engine()

    def _update_signals(self, dt: float):
        for intersection in self.intersections.values():
            if intersection.mode not in [IntersectionMode.FIXED, IntersectionMode.AI_OPTIMIZED, IntersectionMode.MANUAL]:
                continue
                
            intersection.timer -= dt
            if intersection.timer <= 0:
                self._switch_signal_phase(intersection)

    def _is_ns_edge(self, source_id: str, target_id: str) -> bool:
        src = topology_signals.get(source_id)
        tgt = topology_signals.get(target_id)
        if src and tgt:
             dy = abs(src["lat"] - tgt["lat"])
             dx = abs(src["lng"] - tgt["lng"])
             return dy > dx
        return False

    def _calculate_congestion_score(self, target_id: str, is_ns: bool) -> float:
        count: int = 0
        waiting: int = 0
        radius = config.CONGESTION_RADIUS
        
        for v in self.vehicles:
            if v.edge_target == target_id:
                edge_dist = self._get_edge_distance(v.edge_source, v.edge_target)
                dist_to_int = edge_dist - v.position
                
                if dist_to_int < radius:
                    if self._is_ns_edge(v.edge_source, v.edge_target) == is_ns:
                        count += 1
                        if v.speed < 1.0:
                            waiting += 1
                        
        return count + (waiting * 2)

    def _run_ai_decision_engine(self):
        total_ns_score = 0
        total_ew_score = 0
        max_lane_score = -1
        max_lane_id = "None"
        
        for intersection in self.intersections.values():
            if intersection.mode != IntersectionMode.AI_OPTIMIZED:
                continue
                
            ns_score = self._calculate_congestion_score(intersection.id, True)
            ew_score = self._calculate_congestion_score(intersection.id, False)
            
            total_ew_score += ew_score
            total_ns_score += ns_score
            
            if ew_score > max_lane_score:
                max_lane_score = ew_score
                max_lane_id = f"EW @ {intersection.id}"
            if ns_score > max_lane_score:
                max_lane_score = ns_score
                max_lane_id = f"NS @ {intersection.id}"

        recommended = "Balanced"
        green_increase = 0
        efficiency = 0
        
        if total_ns_score > total_ew_score:
            recommended = "North-South"
            green_increase = 5
            efficiency = int((total_ns_score - total_ew_score) * 2) 
        elif total_ew_score > total_ns_score:
            recommended = "East-West"
            green_increase = 5
            efficiency = int((total_ew_score - total_ns_score) * 2)
        
        current_time = time.time()
        if not hasattr(self, "_last_ai_update"):
            self._last_ai_update = 0
            
        if current_time - self._last_ai_update > config.AI_UPDATE_INTERVAL:
            self._last_ai_update = current_time
            
            for intersection in self.intersections.values():
                 if intersection.mode == IntersectionMode.AI_OPTIMIZED:
                     if recommended == "North-South":
                         intersection.nsGreenTime = min(config.MAX_GREEN_TIME, intersection.nsGreenTime + 1.0)
                         intersection.ewGreenTime = max(config.MIN_GREEN_TIME, intersection.ewGreenTime - 1.0)
                     elif recommended == "East-West":
                         intersection.ewGreenTime = min(config.MAX_GREEN_TIME, intersection.ewGreenTime + 1.0)
                         intersection.nsGreenTime = max(config.MIN_GREEN_TIME, intersection.nsGreenTime - 1.0)

        level = "Low"
        if max_lane_score > 10: level = "Medium"
        if max_lane_score > 20: level = "High"

        rec_action = "Monitor"
        rec_value = "--"
        
        if recommended == "North-South":
             rec_action = "Extend North-South Green"
             rec_value = f"+{green_increase}s"
        elif recommended == "East-West":
             rec_action = "Extend East-West Green"
             rec_value = f"+{green_increase}s"

        self.ai_status = AIStatus(
            congestionLevel=level,
            prediction=AIPrediction(
                location=max_lane_id if max_lane_score > 5 else "Grid Optimal",
                time=int(max(0.0, 10.0 - efficiency/10.0))
            ),
            recommendation=AIRecommendation(
                action=rec_action,
                value=rec_value
            ),
            efficiency=efficiency,
            aiActive=self.ai_mode,
            timestamp=current_time
        )

    def _calculate_density(self, intersection_id: str):
        ns_load = 0
        ew_load = 0
        radius = config.DETECTION_RADIUS
        
        for v in self.vehicles:
            if v.edge_target == intersection_id:
                edge_dist = self._get_edge_distance(v.edge_source, v.edge_target)
                dist_to_int = edge_dist - v.position
                if dist_to_int < radius:
                    if self._is_ns_edge(v.edge_source, v.edge_target):
                        ns_load += 1
                    else:
                        ew_load += 1
        return ns_load, ew_load

    def _optimize_signals(self, intersection: Intersection):
        ns_load, ew_load = self._calculate_density(intersection.id)
        
        step = 5.0
        min_green = config.MIN_GREEN_TIME
        max_green = config.MAX_GREEN_TIME
        
        if ns_load > ew_load:
            intersection.nsGreenTime = min(max_green, intersection.nsGreenTime + step)
            intersection.ewGreenTime = max(min_green, intersection.ewGreenTime - step)
        elif ew_load > ns_load:
             intersection.ewGreenTime = min(max_green, intersection.ewGreenTime + step)
             intersection.nsGreenTime = max(min_green, intersection.nsGreenTime - step)

    def _switch_signal_phase(self, intersection: Intersection):
        if intersection.mode == IntersectionMode.AI_OPTIMIZED:
            self._optimize_signals(intersection)

        if intersection.nsSignal == SignalState.GREEN:
            intersection.nsSignal = SignalState.YELLOW
            intersection.timer = config.YELLOW_TIME
        elif intersection.nsSignal == SignalState.YELLOW:
            intersection.nsSignal = SignalState.RED
            intersection.ewSignal = SignalState.GREEN
            intersection.timer = intersection.ewGreenTime
        elif intersection.ewSignal == SignalState.GREEN:
            intersection.ewSignal = SignalState.YELLOW
            intersection.timer = config.YELLOW_TIME
        elif intersection.ewSignal == SignalState.YELLOW:
            intersection.ewSignal = SignalState.RED
            intersection.nsSignal = SignalState.GREEN
            intersection.timer = intersection.nsGreenTime
        elif intersection.nsSignal == SignalState.RED and intersection.ewSignal == SignalState.RED:
             intersection.nsSignal = SignalState.GREEN
             intersection.timer = intersection.nsGreenTime

    def _update_vehicles(self, dt: float):
        vehicles_by_edge: Dict[tuple, List[Vehicle]] = {}
        for v in self.vehicles:
            edge_key = (v.edge_source, v.edge_target)
            if edge_key not in vehicles_by_edge:
                vehicles_by_edge[edge_key] = []
            vehicles_by_edge[edge_key].append(v)

        for (source_id, target_id), edge_vehicles in vehicles_by_edge.items():
            edge_vehicles.sort(key=lambda v: v.position, reverse=True)
            
            edge_dist = self._get_edge_distance(source_id, target_id)
            target_intersection = self.intersections.get(target_id)
            
            for i, v in enumerate(edge_vehicles):
                target_speed = v.target_speed
                stop_pos = -1
                
                if target_intersection:
                    is_ns = self._is_ns_edge(source_id, target_id)
                    should_stop = False
                    if is_ns:
                        if target_intersection.nsSignal in [SignalState.RED, SignalState.YELLOW]:
                            should_stop = True
                    else:
                        if target_intersection.ewSignal in [SignalState.RED, SignalState.YELLOW]:
                            should_stop = True
                            
                    if should_stop:
                        stop_pos = edge_dist - config.STOP_OFFSET
                        if v.position > (edge_dist - config.STOP_OFFSET/2): 
                            stop_pos = -1

                if i > 0:
                    lead_vehicle = edge_vehicles[i-1]
                    lead_stop_pos = lead_vehicle.position - config.MIN_GAP
                    if stop_pos == -1 or lead_stop_pos < stop_pos:
                        stop_pos = lead_stop_pos

                if stop_pos != -1:
                    dist_to_stop = stop_pos - v.position
                    if dist_to_stop < 1.0:
                        v.speed = 0.0
                        v.position = stop_pos
                    elif dist_to_stop < 150.0: 
                        safe_speed = max(0, (2 * config.DECELERATION * dist_to_stop)) ** 0.5 * 0.8
                        if v.speed > safe_speed:
                            required_decel = (v.speed ** 2) / max(0.1, 2 * dist_to_stop)
                            v.speed -= required_decel * dt
                            if v.speed < 0: v.speed = 0.0
                        else:
                            if v.speed < target_speed and v.speed < safe_speed * 0.9:
                                 v.speed += config.ACCELERATION * dt
                else:
                    if v.speed < target_speed:
                        v.speed += config.ACCELERATION * dt
                        if v.speed > target_speed: v.speed = target_speed

                v.position += v.speed * dt

                # check out of bounds if something went wrong
                if v.position < 0: v.position = 0

                if v.position >= edge_dist:
                    neighbors = [adj for adj in adjacency.get(target_id, []) if adj["target"] != source_id]
                    if neighbors:
                        next_edge = random.choice(neighbors)
                        v.edge_source = target_id
                        v.edge_target = next_edge["target"]
                        v.position = 0.0
                    else:
                        self.vehicles.remove(v)
                        self._spawn_vehicle()

        if len(self.vehicles) < config.MIN_SPAWN_VEHICLES and random.random() < config.SPAWN_CHANCE:
            self._spawn_vehicle()

    def get_state(self) -> GridState:
        return GridState(
            intersections=list(self.intersections.values()),
            vehicles=self.vehicles,
            emergency=self.emergency_vehicle
        )

    def get_intersection(self, intersection_id: str) -> Optional[Intersection]:
        return self.intersections.get(intersection_id)

    def update_signal_timing(self, intersection_id: str, updates: SignalUpdate):
        intersection = self.intersections.get(intersection_id)
        if not intersection:
            return None
        
        if updates.nsGreenTime is not None:
            intersection.nsGreenTime = updates.nsGreenTime
        if updates.ewGreenTime is not None:
            intersection.ewGreenTime = updates.ewGreenTime
        if updates.mode is not None:
            intersection.mode = updates.mode
        
        return intersection

    def set_ai_mode(self, enabled: bool):
        self.ai_mode = enabled
        new_mode = IntersectionMode.AI_OPTIMIZED if enabled else IntersectionMode.FIXED
        for intersection in self.intersections.values():
            intersection.mode = new_mode

    def start_emergency(self, route=None):
        if not route or len(route) < 2:
            route = ["S34", "S1", "S17", "S18", "S52"] 
        
        self.emergency_vehicle = EmergencyVehicle(
            id="EM-1",
            position=0.0, 
            edge_source=route[0],
            edge_target=route[1],
            speed=35.0, 
            route=route,
            active=True,
            current_target_index=1,
            type="emergency"
        )
        print(f"Emergency Vehicle Started on route {route}")

    def stop_emergency(self):
        if self.emergency_vehicle is None:
            return

        self.emergency_vehicle.active = False
        for iid in self.emergency_vehicle.route:
            if iid in self.intersections and self.emergency_vehicle:
                if self.intersections[iid].mode == IntersectionMode.EMERGENCY_OVERRIDE:
                    self.intersections[iid].mode = IntersectionMode.FIXED
        
        self.emergency_vehicle = None
        print("Emergency Vehicle Stopped")

    def _update_emergency_vehicle(self, dt: float):
        if self.emergency_vehicle is None:
            return
            
        ev = self.emergency_vehicle
        ev.position += ev.speed * dt
        
        edge_dist = self._get_edge_distance(ev.edge_source, ev.edge_target)
        target_id = ev.edge_target
        intersection = self.intersections.get(target_id)
        
        if intersection:
            dist_to_int = edge_dist - ev.position
            
            if 0 < dist_to_int < config.EMERGENCY_DETECTION_DIST:
                if intersection.mode != IntersectionMode.EMERGENCY_OVERRIDE:
                    intersection.mode = IntersectionMode.EMERGENCY_OVERRIDE
                    is_ns = self._is_ns_edge(ev.edge_source, ev.edge_target)
                    if is_ns:
                        intersection.nsSignal = SignalState.GREEN
                        intersection.ewSignal = SignalState.RED
                    else:
                        intersection.ewSignal = SignalState.GREEN
                        intersection.nsSignal = SignalState.RED
                    print(f"Override {target_id} for Emergency")

        if ev.position >= edge_dist:
            if intersection and intersection.mode == IntersectionMode.EMERGENCY_OVERRIDE:
                 intersection.mode = IntersectionMode.FIXED 
                 print(f"Restore {target_id} after Emergency passed")
            
            ev.current_target_index += 1
            if ev.current_target_index < len(ev.route):
                ev.edge_source = ev.edge_target
                ev.edge_target = ev.route[ev.current_target_index]
                ev.position = 0.0
            else:
                self.stop_emergency()

    def get_ai_status(self) -> AIStatus:
        if self.ai_status:
             return self.ai_status
        return {
            "congestionLevel": "Low",
            "prediction": {"location": "--", "time": 0},
            "recommendation": {"action": "Monitor", "value": "--"},
            "efficiency": 0,
            "aiActive": False
        }

    def get_grid_overview(self) -> GridOverview:
        roads: List[RoadOverview] = []
        zones = [
            ZoneOverview(name="North District", load=0.5, status="optimal"),
            ZoneOverview(name="Central Area", load=0.5, status="optimal"),
            ZoneOverview(name="South Harbor", load=0.5, status="optimal")
        ]
        return GridOverview(roads=roads, zones=zones)

    def get_intersections_list(self) -> List[IntersectionSummary]:
        summary_list = []
        sorted_ids = sorted(self.intersections.keys())
        for i_id in sorted_ids:
            summary_list.append(IntersectionSummary(
                id=i_id,
                name=f"Intersection {i_id}",
                status="active" 
            ))
        return summary_list

    def apply_traffic_pattern(self, pattern: str) -> int:
        ns_green = 10
        ew_green = 10
        
        if pattern == "rush_hour":
            ns_green = 40
            ew_green = 20
        elif pattern == "night_mode":
            ns_green = 10
            ew_green = 10
        elif pattern == "event":
            ns_green = 35
            ew_green = 35
        elif pattern == "holiday":
            ns_green = 20
            ew_green = 20
        else:
            return 0
            
        count = 0
        for intersection in self.intersections.values():
            intersection.nsGreenTime = float(ns_green)
            intersection.ewGreenTime = float(ew_green)
            
            if intersection.nsSignal in [SignalState.GREEN, SignalState.YELLOW]:
                 intersection.timer = float(ns_green)
            else:
                 intersection.timer = float(ew_green)
            count += 1
            
        return count

    def get_intersection_details(self, intersection_id: str) -> Optional[SignalDetails]:
        intersection = self.intersections.get(intersection_id)
        if not intersection:
            return None
            
        phase = "All-Red"
        if intersection.nsSignal == SignalState.GREEN:
            phase = "NS"
        elif intersection.ewSignal == SignalState.GREEN:
            phase = "EW"
        elif intersection.nsSignal == SignalState.YELLOW:
            phase = "NS-Yellow"
        elif intersection.ewSignal == SignalState.YELLOW:
            phase = "EW-Yellow"
        
        flow_rate = random.randint(500, 1000)

        return SignalDetails(
            intersectionId=intersection.id,
            nsGreenTime=int(intersection.nsGreenTime),
            ewGreenTime=int(intersection.ewGreenTime),
            currentPhase=phase,
            timerRemaining=max(0, int(intersection.timer)),
            flowRate=flow_rate,
            pedestrianDemand="Low",
            aiEnabled=(intersection.mode == IntersectionMode.AI_OPTIMIZED)
        )

    def force_ai_optimization(self) -> int:
        count = 0
        for intersection in self.intersections.values():
            intersection.mode = IntersectionMode.AI_OPTIMIZED
            intersection.nsGreenTime = 25.0
            intersection.ewGreenTime = 25.0
            count += 1
        return count

simulation_engine = SimulationEngine()
