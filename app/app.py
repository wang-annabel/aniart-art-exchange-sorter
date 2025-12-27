from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
import shutil
import os
import uuid
import tempfile
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import create_db_and_tables, get_async_session, User
import app.matching as matching
from app.schemas import MatchResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# endpoint sketching

'''how are input.csv and output.csv handled? each generated matching overwrites
the last output.csv, but the user doesn't care about anything past that,
so no need to store in db...'''
matching_cache = set()

@app.post('/matchings')
async def create_matching(file: UploadFile = File(...),
                      session: AsyncSession = Depends(get_async_session)) -> MatchResponse:
    '''User uploads a .csv file. If valid, it gets parsed into the
    input.csv format, then passed through
    the matching algorithm, which generates an output.csv file'''
    temp_input = tempfile.NamedTemporaryFile(delete = False, suffix=os.path.splitext(file.filename)[1])
    try:
        shutil.copyfileobj(file.file, temp_input)
        temp_input.close()

        # check for input.csv format

        # convert to input format
        input_df = matching.form_response_to_input(temp_input.name)

        # merge with prev data

        # Save processed input
        matching_id = str(uuid.uuid4())
        input_path = f'generated/input_{matching_id}.csv'
        input_df.to_csv(input_path, index = False)

        # attempt matching
        raw = [i[1] for i in input_df.iterrows()]
        artists = [matching.Artist(i) for i in raw]

        success = False
        NUM_ATTEMPTS = 100
        for _ in range(NUM_ATTEMPTS):
            match_results = matching.run(artists)

            if match_results['success']:
                success = True
                break

        # store in matching cache
        return {
                'matching_id': matching_id,
                'success': match_results['success'],
                'matched_count': len(match_results['assignments']),
                'total_count': len(artists),
                'unmatched': [
        {'name': artist.name, 'email': artist.email, 'discord': artist.discord}
        for artist in match_results['failed']]
        }

    except TypeError: # non-csv upload
        raise HTTPException(status_code=400, detail='Invalid file type. Please upload a CSV file.')
    except KeyError as e: # invalid csv format (missing columns)
        raise HTTPException(status_code=422, detail=f'Invalid CSV format. Missing required column {str(e)}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally: #cleanup
        if temp_input.name and os.path.exists(temp_input.name):
            os.unlink(temp_input.name)
        file.file.close()

@app.get('/matchings/{matching_id}')
async def get_matching(matching_id: str):
    '''Returns details of a matching attempt.
    Returns data for a graph visualization'''
    pass


@app.post('/matchings/{matching_id}/confirm')
async def confirm_matching():
    '''User confirms the matching. Matches are committed to the previously_assigned table.'''
    pass

@app.get('/matchings/{matching_id}/download')
async def download_output(matching_id: str):
    ''' Returns output.csv file for download.'''
    pass


