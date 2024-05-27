from fastapi import FastAPI
import contextlib
from app.settings import settings
from app.checking.endpoints import router as checking_router
from app.synthetic.endpoints import router as synthetic_router
from app import server_management


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.server_manager = server_management.ServerManager()
    yield
    await app.state.server_manager.stop_server()


app = FastAPI(title="Validator Checking server!", debug=settings.debug, lifespan=lifespan)

app.include_router(checking_router)
app.include_router(synthetic_router)
