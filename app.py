# app.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Query, Body, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging
from typing import Optional, List, Dict, Any
import json
from datetime import datetime

from Sports.manager import sports_manager
from core.database import get_db, init_db, check_db_connection

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Winners Formula API",
    description="Sports betting analytics and formula management API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates (optional - for HTML forms)
# If you want HTML forms, create a templates folder
# templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing PostgreSQL database...")
    try:
        init_db()
        logger.info("Database initialized successfully")
        if check_db_connection():
            logger.info("PostgreSQL connection successful")
        else:
            logger.error("PostgreSQL connection failed")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

# Import routers
from routers import auth, users, formulas, stats

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(formulas.router)
app.include_router(stats.router)

# ============ Pydantic Models for Manual Input ============
class GamelineInput(BaseModel):
    game_id: Optional[str] = None
    game_date: str
    start_time: Optional[str] = None
    home_team_id: str
    away_team_id: str
    home_abbr: Optional[str] = None
    away_abbr: Optional[str] = None
    home_ml: Optional[int] = None
    away_ml: Optional[int] = None
    home_spread: Optional[float] = None
    away_spread: Optional[float] = None
    home_spread_odds: Optional[int] = None
    away_spread_odds: Optional[int] = None
    total: Optional[float] = None
    over_odds: Optional[int] = None
    under_odds: Optional[int] = None
    is_completed: Optional[bool] = False

# ============ Manual Input HTML Form Routes ============
@app.get("/manual/{sport}", response_class=HTMLResponse)
async def manual_input_form(request: Request, sport: str):
    """HTML form for manually inputting a single gameline"""
    if sport not in sports_manager.SUPPORTED_SPORTS:
        return HTMLResponse(content=f"""
        <html>
            <head>
                <title>Invalid Sport</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .error {{ color: #d32f2f; background: #ffebee; padding: 15px; border-radius: 4px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>❌ Invalid Sport</h1>
                    <div class="error">Sport '{sport}' is not supported. Supported sports: {', '.join(sports_manager.SUPPORTED_SPORTS)}</div>
                    <p><a href="/manual">← Back to sport selection</a></p>
                </div>
            </body>
        </html>
        """)
    
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manual Gameline Input - {sport.upper()}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f0f2f5;
                padding: 20px;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #1a1a2e;
                border-bottom: 3px solid #A31D1D;
                padding-bottom: 15px;
                margin-bottom: 25px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .sport-badge {{
                background: #A31D1D;
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 14px;
            }}
            .form-group {{
                margin-bottom: 20px;
            }}
            label {{
                display: block;
                font-weight: 600;
                margin-bottom: 5px;
                color: #333;
                font-size: 14px;
            }}
            label .required {{
                color: #d32f2f;
            }}
            input, select, textarea {{
                width: 100%;
                padding: 10px 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 14px;
                transition: border-color 0.3s;
            }}
            input:focus, select:focus, textarea:focus {{
                outline: none;
                border-color: #A31D1D;
            }}
            .form-row {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }}
            .form-row-3 {{
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 20px;
            }}
            .form-row-4 {{
                display: grid;
                grid-template-columns: 1fr 1fr 1fr 1fr;
                gap: 20px;
            }}
            .btn {{
                background: #A31D1D;
                color: white;
                border: none;
                padding: 14px 30px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: background 0.3s;
                width: 100%;
            }}
            .btn:hover {{
                background: #7a1515;
            }}
            .btn-secondary {{
                background: #6c757d;
                margin-top: 10px;
            }}
            .btn-secondary:hover {{
                background: #5a6268;
            }}
            .btn-group {{
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }}
            .btn-group .btn {{
                flex: 1;
            }}
            .info-box {{
                background: #e3f2fd;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 20px;
                border-left: 4px solid #1976d2;
            }}
            .info-box h3 {{
                color: #1976d2;
                margin-bottom: 5px;
            }}
            .info-box p {{
                color: #333;
                font-size: 14px;
            }}
            .json-input {{
                font-family: 'Courier New', monospace;
                min-height: 200px;
                background: #f8f9fa;
            }}
            .success {{
                background: #d4edda;
                color: #155724;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 20px;
                border: 1px solid #c3e6cb;
            }}
            .error {{
                background: #f8d7da;
                color: #721c24;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 20px;
                border: 1px solid #f5c6cb;
            }}
            .nav-links {{
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                display: flex;
                gap: 15px;
            }}
            .nav-links a {{
                color: #A31D1D;
                text-decoration: none;
                font-weight: 500;
            }}
            .nav-links a:hover {{
                text-decoration: underline;
            }}
            @media (max-width: 600px) {{
                .form-row, .form-row-3, .form-row-4 {{
                    grid-template-columns: 1fr;
                }}
                .container {{
                    padding: 15px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>
                📝 Manual Gameline Input
                <span class="sport-badge">{sport.upper()}</span>
            </h1>
            
            <div class="info-box">
                <h3>ℹ️ Instructions</h3>
                <p>Fill in the form below to manually add a gameline. Required fields are marked with <span style="color:#d32f2f;">*</span></p>
            </div>
            
            <form id="gamelineForm" action="/{sport}/gamelines/manual" method="POST" onsubmit="return submitForm(event)">
                <div class="form-row">
                    <div class="form-group">
                        <label>Game Day <span class="required">*</span></label>
                        <input type="date" name="game_date" required value="{datetime.now().strftime('%Y-%m-%d')}">
                    </div>
                    <div class="form-group">
                        <label>Start Time</label>
                        <input type="time" name="start_time" placeholder="13:00">
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label>Home Team <span class="required">*</span></label>
                        <input type="text" name="home_team_id" placeholder="Detroit Lions" required>
                    </div>
                    <div class="form-group">
                        <label>Away Team <span class="required">*</span></label>
                        <input type="text" name="away_team_id" placeholder="Green Bay Packers" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label>Home Abbreviation</label>
                        <input type="text" name="home_abbr" placeholder="DET">
                    </div>
                    <div class="form-group">
                        <label>Away Abbreviation</label>
                        <input type="text" name="away_abbr" placeholder="GB">
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label>Home Moneyline</label>
                        <input type="number" name="home_ml" placeholder="-150">
                    </div>
                    <div class="form-group">
                        <label>Away Moneyline</label>
                        <input type="number" name="away_ml" placeholder="+130">
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label>Home Spread</label>
                        <input type="number" step="0.5" name="home_spread" placeholder="-3.5">
                    </div>
                    <div class="form-group">
                        <label>Away Spread</label>
                        <input type="number" step="0.5" name="away_spread" placeholder="+3.5">
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label>Home Spread Odds</label>
                        <input type="number" name="home_spread_odds" placeholder="-110">
                    </div>
                    <div class="form-group">
                        <label>Away Spread Odds</label>
                        <input type="number" name="away_spread_odds" placeholder="-110">
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label>Total</label>
                        <input type="number" step="0.5" name="total" placeholder="44.5">
                    </div>
                    <div class="form-group">
                        <label>Game ID (optional)</label>
                        <input type="text" name="game_id" placeholder="auto-generated if blank">
                    </div>
                </div>
                
                <div class="form-row-3">
                    <div class="form-group">
                        <label>Over Odds</label>
                        <input type="number" name="over_odds" placeholder="-110">
                    </div>
                    <div class="form-group">
                        <label>Under Odds</label>
                        <input type="number" name="under_odds" placeholder="-110">
                    </div>
                    <div class="form-group">
                        <label>Completed?</label>
                        <select name="is_completed">
                            <option value="false">No</option>
                            <option value="true">Yes</option>
                        </select>
                    </div>
                </div>
                
                <div id="responseMessage"></div>
                
                <button type="submit" class="btn">➕ Add Gameline</button>
            </form>
            
            <div style="margin-top: 20px;">
                <a href="/manual/{sport}/bulk" class="btn btn-secondary" style="display: block; text-align: center; color: white; text-decoration: none;">
                    📦 Bulk Import Instead
                </a>
            </div>
            
            <div class="nav-links">
                <a href="/manual">← Select Different Sport</a>
                <a href="/docs">📚 API Documentation</a>
                <a href="/{sport}/gamelines">📊 View {sport.upper()} Gamelines</a>
            </div>
        </div>
        
        <script>
            async function submitForm(event) {{
                event.preventDefault();
                
                const form = document.getElementById('gamelineForm');
                const formData = new FormData(form);
                const data = {{}};
                
                // Convert FormData to JSON
                for (const [key, value] of formData.entries()) {{
                    if (value !== '') {{
                        // Convert boolean strings
                        if (key === 'is_completed') {{
                            data[key] = value === 'true';
                        }} else if (!isNaN(value) && value !== '' && key !== 'game_date' && key !== 'start_time' && key !== 'game_id') {{
                            data[key] = parseFloat(value);
                        }} else {{
                            data[key] = value;
                        }}
                    }}
                }}
                
                const responseDiv = document.getElementById('responseMessage');
                
                try {{
                    const response = await fetch(form.action, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify(data)
                    }});
                    
                    const result = await response.json();
                    
                    if (response.ok) {{
                        responseDiv.innerHTML = `<div class="success">✅ ${{result.message}}</div>`;
                        if (result.game) {{
                            responseDiv.innerHTML += `<div class="success" style="background:#e8f5e9;border-color:#81c784;"><pre style="margin:0;font-size:12px;">${{JSON.stringify(result.game, null, 2)}}</pre></div>`;
                        }}
                        form.reset();
                    }} else {{
                        responseDiv.innerHTML = `<div class="error">❌ Error: ${{result.detail || result.error || 'Unknown error'}}</div>`;
                    }}
                }} catch (error) {{
                    responseDiv.innerHTML = `<div class="error">❌ Network Error: ${{error.message}}</div>`;
                }}
                
                return false;
            }}
        </script>
    </body>
    </html>
    """)

@app.get("/manual/{sport}/bulk", response_class=HTMLResponse)
async def manual_input_bulk_form(request: Request, sport: str):
    """HTML form for bulk manual input of gamelines"""
    if sport not in sports_manager.SUPPORTED_SPORTS:
        return HTMLResponse(content=f"""
        <html>
            <head>
                <title>Invalid Sport</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .error {{ color: #d32f2f; background: #ffebee; padding: 15px; border-radius: 4px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>❌ Invalid Sport</h1>
                    <div class="error">Sport '{sport}' is not supported. Supported sports: {', '.join(sports_manager.SUPPORTED_SPORTS)}</div>
                    <p><a href="/manual">← Back to sport selection</a></p>
                </div>
            </body>
        </html>
        """)
    
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bulk Manual Input - {sport.upper()}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f0f2f5;
                padding: 20px;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #1a1a2e;
                border-bottom: 3px solid #A31D1D;
                padding-bottom: 15px;
                margin-bottom: 25px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .sport-badge {{
                background: #A31D1D;
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 14px;
            }}
            .form-group {{
                margin-bottom: 20px;
            }}
            label {{
                display: block;
                font-weight: 600;
                margin-bottom: 5px;
                color: #333;
                font-size: 14px;
            }}
            textarea {{
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 13px;
                font-family: 'Courier New', monospace;
                min-height: 350px;
                transition: border-color 0.3s;
                background: #f8f9fa;
            }}
            textarea:focus {{
                outline: none;
                border-color: #A31D1D;
            }}
            .btn {{
                background: #A31D1D;
                color: white;
                border: none;
                padding: 14px 30px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: background 0.3s;
                width: 100%;
            }}
            .btn:hover {{
                background: #7a1515;
            }}
            .btn-secondary {{
                background: #6c757d;
                margin-top: 10px;
            }}
            .btn-secondary:hover {{
                background: #5a6268;
            }}
            .btn-group {{
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }}
            .btn-group .btn {{
                flex: 1;
            }}
            .info-box {{
                background: #e3f2fd;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 20px;
                border-left: 4px solid #1976d2;
            }}
            .info-box h3 {{
                color: #1976d2;
                margin-bottom: 5px;
            }}
            .info-box p {{
                color: #333;
                font-size: 14px;
            }}
            .info-box code {{
                background: #f5f5f5;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 12px;
            }}
            .success {{
                background: #d4edda;
                color: #155724;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 20px;
                border: 1px solid #c3e6cb;
            }}
            .error {{
                background: #f8d7da;
                color: #721c24;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 20px;
                border: 1px solid #f5c6cb;
            }}
            .nav-links {{
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                display: flex;
                gap: 15px;
            }}
            .nav-links a {{
                color: #A31D1D;
                text-decoration: none;
                font-weight: 500;
            }}
            .nav-links a:hover {{
                text-decoration: underline;
            }}
            .example {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                margin-top: 10px;
                border: 1px solid #e0e0e0;
            }}
            .example pre {{
                margin: 0;
                font-size: 12px;
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 15px;
                margin-bottom: 20px;
            }}
            .stat-card {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                text-align: center;
                border: 1px solid #e0e0e0;
            }}
            .stat-card .number {{
                font-size: 28px;
                font-weight: bold;
                color: #A31D1D;
            }}
            .stat-card .label {{
                font-size: 12px;
                color: #666;
                margin-top: 5px;
            }}
            @media (max-width: 600px) {{
                .stats {{
                    grid-template-columns: 1fr 1fr;
                }}
                .container {{
                    padding: 15px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>
                📦 Bulk Manual Gameline Input
                <span class="sport-badge">{sport.upper()}</span>
            </h1>
            
            <div class="info-box">
                <h3>ℹ️ Instructions</h3>
                <p>
                    Paste a JSON array of gameline objects below. Each object should contain the same fields as the single form.
                    Required fields: <code>game_date</code>, <code>home_team_id</code>, <code>away_team_id</code>
                </p>
            </div>
            
            <div id="responseMessage"></div>
            
            <form id="bulkForm" action="/{sport}/gamelines/manual/bulk" method="POST" onsubmit="return submitBulkForm(event)">
                <div class="form-group">
                    <label>JSON Data <span class="required">*</span></label>
                    <textarea id="jsonData" name="json_data" required placeholder='[
                    {{
                        "game_date": "{datetime.now().strftime('%Y-%m-%d')}",
                        "home_team_id": "Detroit Lions",
                        "away_team_id": "Green Bay Packers",
                        "home_abbr": "DET",
                        "away_abbr": "GB",
                        "home_spread": -3.5,
                        "over_under": 44.5
                    }},
                    {{
                        "game_date": "{datetime.now().strftime('%Y-%m-%d')}",
                        "home_team_id": "Kansas City Chiefs",
                        "away_team_id": "Denver Broncos",
                        "home_abbr": "KC",
                        "away_abbr": "DEN",
                        "home_spread": -2.5,
                        "total": 42.5
                    }}
                ]'></textarea>
                </div>
                
                <div class="example">
                    <strong>📋 Example JSON:</strong>
                    <pre>[
                    {{
                        "game_date": "{datetime.now().strftime('%Y-%m-%d')}",
                        "home_team_id": "Detroit Lions",
                        "away_team_id": "Green Bay Packers",
                        "home_abbr": "DET",
                        "away_abbr": "GB",
                        "home_ml": -150,
                        "away_ml": 130,
                        "home_spread": -3.5,
                        "away_spread": 3.5,
                        "home_spread_odds": -110,
                        "away_spread_odds": -110,
                        "total": 44.5,
                        "over_odds": -110,
                        "under_odds": -110
                    }},
                    {{
                        "game_date": "{datetime.now().strftime('%Y-%m-%d')}",
                        "home_team_id": "Kansas City Chiefs",
                        "away_team_id": "Denver Broncos",
                        "home_abbr": "KC",
                        "away_abbr": "DEN",
                        "home_spread": -2.5,
                        "total": 42.5
                    }}
                ]</pre>
                </div>
                
                <button type="submit" class="btn">📥 Import Bulk Gamelines</button>
            </form>
            
            <div style="margin-top: 20px;">
                <a href="/manual/{sport}" class="btn-secondary" style="display: block; text-align: center; color: white; text-decoration: none; padding: 14px 30px; border-radius: 6px; background: #6c757d;">
                    📝 Single Input Instead
                </a>
            </div>
            
            <div class="nav-links">
                <a href="/manual">← Select Different Sport</a>
                <a href="/docs">📚 API Documentation</a>
                <a href="/{sport}/gamelines">📊 View {sport.upper()} Gamelines</a>
            </div>
        </div>
        
        <script>
            async function submitBulkForm(event) {{
                event.preventDefault();
                
                const textarea = document.getElementById('jsonData');
                const responseDiv = document.getElementById('responseMessage');
                
                try {{
                    const data = JSON.parse(textarea.value);
                    
                    if (!Array.isArray(data)) {{
                        responseDiv.innerHTML = `<div class="error">❌ Error: Data must be an array of games</div>`;
                        return;
                    }}
                    
                    const response = await fetch('/{sport}/gamelines/manual/bulk', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify(data)
                    }});
                    
                    const result = await response.json();
                    
                    if (response.ok) {{
                        let html = `<div class="success">✅ ${{result.message}}</div>`;
                        html += `<div class="stats">
                            <div class="stat-card"><div class="number">${{result.added || 0}}</div><div class="label">Added</div></div>
                            <div class="stat-card"><div class="number">${{result.errors?.length || 0}}</div><div class="label">Errors</div></div>
                            <div class="stat-card"><div class="number">${{result.total || 0}}</div><div class="label">Total</div></div>
                            <div class="stat-card"><div class="number">${{result.total > 0 ? Math.round((result.added / result.total) * 100) : 0}}%</div><div class="label">Success Rate</div></div>
                        </div>`;
                        
                        if (result.errors && result.errors.length > 0) {{
                            html += `<div class="error"><strong>⚠️ Errors:</strong><pre style="margin:5px 0 0 0;font-size:12px;">${{JSON.stringify(result.errors, null, 2)}}</pre></div>`;
                        }}
                        
                        responseDiv.innerHTML = html;
                        textarea.value = '';
                    }} else {{
                        responseDiv.innerHTML = `<div class="error">❌ Error: ${{result.detail || result.error || 'Unknown error'}}</div>`;
                    }}
                }} catch (error) {{
                    if (error instanceof SyntaxError) {{
                        responseDiv.innerHTML = `<div class="error">❌ JSON Parse Error: ${{error.message}}</div>`;
                    }} else {{
                        responseDiv.innerHTML = `<div class="error">❌ Network Error: ${{error.message}}</div>`;
                    }}
                }}
                
                return false;
            }}
        </script>
    </body>
    </html>
    """)

@app.get("/manual", response_class=HTMLResponse)
async def manual_select_sport(request: Request):
    """Sport selection page for manual input"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Select Sport - Manual Input</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f0f2f5;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #1a1a2e;
                border-bottom: 3px solid #A31D1D;
                padding-bottom: 15px;
                margin-bottom: 30px;
            }
            .sport-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin: 20px 0;
            }
            .sport-card {
                background: #f8f9fa;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 25px;
                text-align: center;
                transition: all 0.3s;
                text-decoration: none;
                color: #333;
            }
            .sport-card:hover {
                border-color: #A31D1D;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            .sport-card .icon {
                font-size: 48px;
                margin-bottom: 10px;
            }
            .sport-card .name {
                font-size: 18px;
                font-weight: bold;
            }
            .sport-card .badge {
                display: inline-block;
                background: #A31D1D;
                color: white;
                padding: 2px 10px;
                border-radius: 12px;
                font-size: 11px;
                margin-top: 5px;
            }
            .info-box {
                background: #e3f2fd;
                padding: 15px;
                border-radius: 6px;
                margin: 20px 0;
                border-left: 4px solid #1976d2;
            }
            .info-box p {
                color: #333;
                font-size: 14px;
            }
            .nav-links {
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                display: flex;
                gap: 15px;
            }
            .nav-links a {
                color: #A31D1D;
                text-decoration: none;
                font-weight: 500;
            }
            .nav-links a:hover {
                text-decoration: underline;
            }
            @media (max-width: 600px) {
                .sport-grid {
                    grid-template-columns: 1fr 1fr;
                }
                .container {
                    padding: 20px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏆 Select Sport for Manual Input</h1>
            
            <div class="info-box">
                <p>Choose a sport to manually add gamelines. You can add single games or bulk import via JSON.</p>
            </div>
            
            <div class="sport-grid">
                <a href="/manual/nfl" class="sport-card">
                    <div class="icon">🏈</div>
                    <div class="name">NFL</div>
                    <div class="badge">Football</div>
                </a>
                <a href="/manual/nba" class="sport-card">
                    <div class="icon">🏀</div>
                    <div class="name">NBA</div>
                    <div class="badge">Basketball</div>
                </a>
                <a href="/manual/mlb" class="sport-card">
                    <div class="icon">⚾</div>
                    <div class="name">MLB</div>
                    <div class="badge">Baseball</div>
                </a>
                <a href="/manual/nhl" class="sport-card">
                    <div class="icon">🏒</div>
                    <div class="name">NHL</div>
                    <div class="badge">Hockey</div>
                </a>
                <a href="/manual/ncaaf" class="sport-card">
                    <div class="icon">🎯</div>
                    <div class="name">NCAAF</div>
                    <div class="badge">College Football</div>
                </a>
                <a href="/manual/ncaab" class="sport-card">
                    <div class="icon">🏀</div>
                    <div class="name">NCAAB</div>
                    <div class="badge">College Basketball</div>
                </a>
            </div>
            
            <div class="nav-links">
                <a href="/docs">📚 API Documentation</a>
                <a href="/">🏠 Home</a>
            </div>
        </div>
    </body>
    </html>
    """)

# ============ API Endpoints for Manual Input ============
@app.post("/{sport}/gamelines/manual")
async def add_manual_gameline_api(
    sport: str,
    game_data: GamelineInput,
    db: Session = Depends(get_db)
):
    """API endpoint to add a single gameline manually"""
    if sport not in sports_manager.SUPPORTED_SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")
    
    result = sports_manager.manual_add_gameline(sport, db, game_data.dict())
    
    if result.get('error'):
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

@app.post("/{sport}/gamelines/manual/bulk")
async def add_manual_gamelines_bulk_api(
    sport: str,
    games_data: List[GamelineInput] = Body(...),
    db: Session = Depends(get_db)
):
    """API endpoint to add multiple gamelines manually from JSON data"""
    if sport not in sports_manager.SUPPORTED_SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")
    
    if not games_data:
        raise HTTPException(status_code=400, detail="No games provided")
    
    # Convert to dict list
    games_dict = [game.dict() for game in games_data]
    
    result = sports_manager.manual_add_gamelines_bulk(sport, db, games_dict)
    
    if result.get('error'):
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

# ============ Gamelines Endpoints ============
@app.get("/{sport}/gamelines")
async def get_sport_gamelines(
    sport: str,
    force_refresh: bool = Query(False, description="Force refresh from web"),
    db: Session = Depends(get_db)
):
    """Get gamelines for a specific sport"""
    if sport not in sports_manager.SUPPORTED_SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")
    
    result = await sports_manager.get_gamelines(sport, db, force_refresh)
    
    if result.get('error'):
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result

@app.get("/{sport}/season-phase")
async def get_season_phase(
    sport: str,
    db: Session = Depends(get_db)
):
    """Get current season phase for a sport"""
    if sport not in sports_manager.SUPPORTED_SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")
    
    result = await sports_manager.get_season_phase(sport, db)
    
    if result.get('error'):
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result

# ============ Sports Endpoints ============
@app.get("/sports")
async def get_supported_sports():
    return {
        'sports': sports_manager.SUPPORTED_SPORTS,
        'count': len(sports_manager.SUPPORTED_SPORTS)
    }

@app.get("/")
async def read_root():
    return {
        "message": "Winners Formula API is running!",
        "version": "2.0.0",
        "documentation": "/docs",
        "manual_input": "/manual",
        "supported_sports": sports_manager.SUPPORTED_SPORTS,
        "database": "PostgreSQL"
    }

from core.database import get_table_schema_json, get_all_schemas_json, get_table_columns

@app.get("/admin/schema")
async def get_database_schema():
    """Get database schema information (for debugging)"""
    return get_all_schemas_json()

@app.get("/admin/schema/{table_name}")
async def get_table_schema(table_name: str):
    """Get schema for a specific table"""
    schema = get_table_schema_json(table_name)
    if not schema['columns']:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    return schema

@app.get("/admin/tables")
async def get_database_tables():
    """Get list of all tables in the database"""
    try:
        from core.database import get_db
        db = next(get_db())
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        db.close()
        return {'tables': tables, 'count': len(tables)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    db_status = check_db_connection()
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "database_type": "PostgreSQL",
        "supported_sports": sports_manager.SUPPORTED_SPORTS
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )