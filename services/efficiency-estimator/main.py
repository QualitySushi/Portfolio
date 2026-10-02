import os
from typing import Any

import numpy as np
import pvlib
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from supabase import Client, create_client

load_dotenv()

app = FastAPI(title="Efficiency Estimator Simulation Service")

# Initialize Supabase client safely with type casting
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
supabase: Client | None = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


# Pydantic model for validating incoming simulation parameters
class SimulationParams(BaseModel):
    module_width: float
    module_length: float
    margin_lr: float
    margin_ud: float
    P1_width: float
    Cell_width: float
    P1_P2: float = Field(..., alias="P1-P2")
    P2_width: float
    P2_P3: float = Field(..., alias="P2-P3")
    P3_width: float
    sheet_ohm: float
    carbon_ohm: float
    shunt: float
    Intrinsic_series: float
    Jsc_norm: float
    dark_sat_norm: float
    V_th: float
    n_ideal: float
    rho_contact: float
    light_intensity: float
    IV_points: int = 100


class BatchSimulationParams(BaseModel):
    base_params: dict[str, Any]  # All standard simulation inputs
    target_variable: str         # e.g., "Cell_width"
    step_size: float             # e.g., 0.025
    num_simulations: int         # e.g., 250


class SaveBatchJobParams(BaseModel):
    target_variable: str
    batch_results: list[dict[str, Any]]
    summary_trend: list[dict[str, Any]] | None = None
    optimal_result: dict[str, Any] | None = None


class PVModuleSimulator:
    def __init__(self, params: dict):
        print(f"[DEBUG PARAMS RECEIVED]: module_length={params.get('module_length')}, margin_ud={params.get('margin_ud')}, Cell_width={params.get('Cell_width')}")
        if params.get('light_intensity', 0.0) == 0.0:
            raise ValueError("light_intensity cannot be zero.")
            
        self.module_width = float(params["module_width"])
        self.module_length = float(params["module_length"])
        self.margin_lr = float(params['margin_lr'])
        self.margin_ud = float(params['margin_ud'])
        self.P1_width = float(params['P1_width'])
        self.active_width = float(params['Cell_width'])
        
        self.distance_P1_P2 = float(params.get('P1-P2', params.get('P1_P2', 0.1)))
        self.P2_width = float(params['P2_width'])
        self.distance_P2_P3 = float(params.get('P2-P3', params.get('P2_P3', 0.1)))
        self.P3_width = float(params['P3_width'])
        
        # Core geometry math
        self.dead_width = (self.P1_width + self.distance_P1_P2 + self.P2_width + self.distance_P2_P3 + self.P3_width)
        self.distance_P1_P1 = self.active_width + self.dead_width
        
        if self.distance_P1_P1 <= 0:
            raise ValueError("Cell pitch (distance_P1_P1) must be greater than zero.")
            
        self.n_cells = int((self.module_width - 2 * self.margin_lr) / self.distance_P1_P1)
        
        if self.n_cells <= 0:
            raise ValueError(f"Invalid geometry: calculated n_cells is {self.n_cells}. Check module width, margins, and cell width.")
            
        self.sheet_ohm = float(params['sheet_ohm'])
        self.carbon_ohm = float(params['carbon_ohm'])
        
        self.shunt = float(params['shunt'])
        self.series_int = float(params['Intrinsic_series'])
        self.Jsc_norm = float(params['Jsc_norm'])
        self.dark_sat_norm = float(params['dark_sat_norm'])
        self.V_th = float(params['V_th'])
        self.n_ideal = float(params['n_ideal'])
        self.rho_contact = float(params['rho_contact'])
        
        self.P_in_density = params['light_intensity']
        self.IV_points = int(params['IV_points'])
        
        self.cell_area = (self.module_length - 2 * self.margin_ud) * self.active_width      
        self.cell_area_cm2 = self.cell_area / 100.0
        
        if self.cell_area_cm2 <= 0:
            raise ValueError("Cell area must be greater than zero.")
            
        self.active_area = self.cell_area * self.n_cells
        
        # R_series calculation
        self.totalITO_width = 0.5 * self.active_width * self.n_cells + (0.5 * self.P2_width + self.distance_P2_P3 + self.P3_width) * (self.n_cells - 1)
        self.totalITO_length = (self.module_length - 2 * self.margin_ud)
        self.sheet_res_scale_factor = self.totalITO_width / self.totalITO_length if self.totalITO_length > 0 else 0.0
        self.carbon_width = 0.5 * self.active_width * self.n_cells + (0.5 * self.P2_width + self.distance_P1_P2 + self.P1_width) * (self.n_cells - 1)
        self.carbon_res_scale_factor = self.carbon_width / self.totalITO_length if self.totalITO_length > 0 else 0.0
        self.P2_resistance = self.rho_contact * (self.n_cells - 1) / (self.P2_width * self.totalITO_length) if (self.P2_width * self.totalITO_length) > 0 else 0.0
        
        self.Rseries_ITO = self.sheet_ohm * self.sheet_res_scale_factor
        self.Rseries_carbon = self.carbon_ohm * self.carbon_res_scale_factor
        self.Rseries_int = self.n_cells * self.series_int / self.cell_area_cm2 
        self.Rseries = self.Rseries_ITO + self.Rseries_carbon + self.P2_resistance + self.Rseries_int
        
        # R_shunt calculation
        self.shunt_resistance = self.n_cells * self.shunt / self.cell_area_cm2  
        if self.shunt_resistance <= 0:
            raise ValueError("Shunt resistance must be greater than zero.")
            
        self.Jsc_mA = self.Jsc_norm * self.cell_area_cm2
        self.Jsc_Amp = self.Jsc_mA / 1000.0
        
        self.dark_sat_mA = self.dark_sat_norm * self.cell_area_cm2
        self.dark_sat_Amp = self.dark_sat_mA / 1000.0
        self.nNVth = self.n_ideal * self.V_th * self.n_cells
        
        self.aperture_area = (self.n_cells * self.cell_area) + (self.totalITO_length * self.dead_width * (self.n_cells - 1))

    def run_simulation(self) -> dict[str, Any]:
        results = pvlib.pvsystem.singlediode(
            self.Jsc_Amp, self.dark_sat_Amp, self.Rseries, self.shunt_resistance, self.nNVth
        )
        
        def safe_float(val: Any) -> float:
            try:
                return float(val.iloc[0]) if hasattr(val, 'iloc') else float(val)
            except (ValueError, TypeError, AttributeError):
                return 0.0

        res_dict = {k: safe_float(v) for k, v in results.items()}
        
        p_out = res_dict.get('v_mp', 0.0) * res_dict.get('i_mp', 0.0)
        p_in = (self.aperture_area * self.P_in_density) / 100000.0
        efficiency = (p_out / p_in) * 100.0 if p_in > 0 else 0.0
        
        act_efficiency = (res_dict.get('p_mp', 0.0) / ((self.active_area * self.P_in_density) / 100000.0)) * 100.0 if self.active_area > 0 else 0.0
        gff = self.active_area / (self.module_width * self.module_length) if (self.module_width * self.module_length) > 0 else 0.0
        aperture_gff = self.active_area / self.aperture_area if self.aperture_area > 0 else 0.0
        
        i_sc = res_dict.get('i_sc', 0.0)
        v_oc = res_dict.get('v_oc', 0.0)
        ff = (p_out / (v_oc * i_sc)) * 100.0 if (v_oc * i_sc) > 0 else 0.0
        
        # Generate IV curve arrays
        voltage_arr = np.linspace(0, v_oc, self.IV_points) if v_oc > 0 else np.zeros(self.IV_points)
        
        raw_current = pvlib.pvsystem.i_from_v(
            voltage_arr, self.Jsc_Amp, self.dark_sat_Amp, self.Rseries, self.shunt_resistance, self.nNVth, method='lambertw'
        )
        current_arr = np.nan_to_num(np.array(raw_current))

        i_x = 0.0
        i_xx = 0.0
        if len(voltage_arr) > 0 and len(current_arr) > 0:
            idx_x = int(len(voltage_arr) * 0.25)
            idx_xx = int(len(voltage_arr) * 0.75)
            i_x = float(current_arr[idx_x])
            i_xx = float(current_arr[idx_xx])

        return {
            "metrics": {
                **res_dict,
                "Pmp": res_dict.get('p_mp', 0.0),
                "Imp": res_dict.get('i_mp', 0.0),
                "Vmp": res_dict.get('v_mp', 0.0),
                "I_x": i_x,
                "I_xx": i_xx,
                "GFF": gff,
                "Efficiency_pct": efficiency,
                "Aperture_Efficiency_pct": efficiency,
                "Active_Area_Efficiency_pct": act_efficiency,
                "Act_Efficiency_pct": act_efficiency,
                "aperture_gff": aperture_gff,
                "Rseries": self.Rseries,
                "Rshunt": self.shunt_resistance,
                "FF_pct": ff,
                "Ncells": self.n_cells
            },
            "iv_curve": {
                "voltage": voltage_arr.tolist(),
                "current": current_arr.tolist()
            }
        }


@app.post("/simulate")
def simulate_endpoint(params: SimulationParams) -> dict[str, Any]:
    try:
        simulator = PVModuleSimulator(params.model_dump(by_alias=True))
        return simulator.run_simulation()
    except (ValueError, TypeError, KeyError) as e:
        print(f"[SIMULATE ERROR DETAIL]: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise


@app.post("/batch-simulate")
def run_batch_simulation(config: BatchSimulationParams) -> dict[str, Any]:
    try:
        current_value = float(config.base_params.get(config.target_variable, 0.0))
        
        batch_results = []
        lightweight_trend = []
        best_run = None
        highest_efficiency = -1.0

        for i in range(config.num_simulations):
            iter_params = config.base_params.copy()
            iter_params[config.target_variable] = current_value
            
            simulator = PVModuleSimulator(iter_params)
            sim_result = simulator.run_simulation()
            
            eff = sim_result["metrics"].get("Efficiency_pct", 0.0)
            pmp = sim_result["metrics"].get("Pmp", 0.0)
            
            run_data = {
                "iteration": i,
                "parameter_value": current_value,
                "metrics": sim_result["metrics"],
                "iv_curve": sim_result["iv_curve"]
            }
            
            batch_results.append(run_data)
            
            if eff > highest_efficiency:
                highest_efficiency = eff
                best_run = run_data
            
            lightweight_trend.append({
                "iteration": i,
                "parameter_value": current_value,
                "Efficiency_pct": eff,
                "Pmp": pmp
            })
            
            current_value += config.step_size
        
        return {
            "batch_id": None,
            "batch_results": batch_results,
            "summary_trend": lightweight_trend,
            "optimal_result": best_run
        }
        
    except (ValueError, TypeError, KeyError) as e:
        print(f"[BATCH ERROR DETAIL]: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[BATCH UNEXPECTED ERROR]: {e}")
        raise HTTPException(status_code=500, detail=f"Simulation error: {e!s}")


# --- NEW ENDPOINT: MANUAL BATCH SAVE ---

@app.post("/batch-jobs")
def save_batch_job(payload: SaveBatchJobParams) -> dict[str, Any]:
    """Manually save batch simulation results and optimal run to Supabase from the frontend button."""
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase is not configured.")
    try:
        trend = payload.summary_trend or [
            {
                "iteration": r.get("iteration"),
                "parameter_value": r.get("parameter_value"),
                "Efficiency_pct": r.get("metrics", {}).get("Efficiency_pct", 0.0),
                "Pmp": r.get("metrics", {}).get("Pmp", 0.0)
            }
            for r in payload.batch_results
        ]
        
        job_response = supabase.table("batch_jobs").insert({
            "target_variable": payload.target_variable,
            "total_iterations": len(payload.batch_results),
            "summary_trend": trend
        }).execute()

        response_data = getattr(job_response, "data", None)
        batch_job_id = None
        if response_data and isinstance(response_data, list) and len(response_data) > 0:
            first_row = response_data[0]
            if isinstance(first_row, dict):
                batch_job_id = first_row.get("id")

        best_run = payload.optimal_result
        if not best_run and payload.batch_results:
            best_run = max(
                payload.batch_results,
                key=lambda r: r.get("metrics", {}).get("Aperture_Efficiency_pct", r.get("metrics", {}).get("Efficiency_pct", 0.0))
            )

        if batch_job_id and best_run:
            supabase.table("optimal_simulations").insert({
                "batch_id": batch_job_id,
                "iteration_index": best_run.get("iteration", 0),
                "parameter_value": best_run.get("parameter_value", 0.0),
                "metrics": best_run.get("metrics", {}),
                "iv_curve": best_run.get("iv_curve", {})
            }).execute()

        return {"status": "success", "batch_id": batch_job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to persist batch job: {e!s}")


# --- RETRIEVAL ENDPOINTS ---

@app.get("/batch-jobs")
def list_batch_jobs(limit: int = 10) -> list[dict[str, Any]]:
    """Retrieve a list of past batch simulation runs for history/dashboard views."""
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase is not configured.")
    try:
        response = supabase.table("batch_jobs").select("id, created_at, target_variable, total_iterations").order("created_at", desc=True).limit(limit).execute()
        
        raw_data = response.data
        if isinstance(raw_data, list):
            return [dict(row) for row in raw_data if isinstance(row, dict)]
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {e!s}")


@app.get("/batch-jobs/{batch_id}")
def get_batch_job_details(batch_id: str) -> dict[str, Any]:
    """Retrieve the full history summary and the optimal simulation configuration for a specific batch ID."""
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase is not configured.")
    try:
        job_res = supabase.table("batch_jobs").select("*").eq("id", batch_id).execute()
        if not job_res.data:
            raise HTTPException(status_code=404, detail="Batch job not found.")
        
        batch_job = job_res.data[0]
        opt_res = supabase.table("optimal_simulations").select("*").eq("batch_id", batch_id).execute()
        optimal_simulation = opt_res.data[0] if opt_res.data else None

        return {
            "batch_metadata": batch_job,
            "optimal_simulation": optimal_simulation
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {e!s}")