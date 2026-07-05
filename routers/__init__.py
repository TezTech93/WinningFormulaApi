# routers/__init__.py
from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.formulas import router as formulas_router
from routers.gamelines import router as gamelines_router
from routers.stats import router as stats_router
from routers.parlays import router as parlays_router
from routers.strategies import router as strategies_router

__all__ = [
    'auth_router',
    'users_router',
    'formulas_router',
    'gamelines_router',
    'stats_router',
    'parlays_router',
    'strategies_router'
]