from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
import shutil
import os
import uuid
import tempfile
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import create_db_and_tables, get_async_session, User

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# endpoint sketching

'''how are input.csv and output.csv handled? each generated matching overwrites
the last output.csv, but the user doesn't care about anything past that,
so no need to store in db...'''

@app.post('/upload')
async def upload_file(file: UploadFile = File(...),
                      session: AsyncSession = Depends(get_async_session)):
    '''User uploads a .csv file. If valid, it gets parsed into the
    input.csv format, then passed through
    the matching algorithm, which generates an output.csv file'''
    # create some kind of graph visualization too... or is that better handled in another endpoint.
    pass

@app.post('/confirm')
async def confirm_matching():
    '''User confirms the matching. Matches are added to the previously_assigned table.'''
    pass

# users might want to discard the matching/reshuffle. what kind of endpoint makes sense here?
@app.put('/retry')
async def retry_matching():
    '''Generates another matching based off the last input.csv'''
    pass


