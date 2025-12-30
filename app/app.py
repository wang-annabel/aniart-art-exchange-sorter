from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from fastapi.responses import FileResponse
import shutil
import os
import uuid
import tempfile
import pandas as pd
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

from app.db import create_db_and_tables, get_async_session, User, PreviouslyAssigned
import app.matching as matching
from app.schemas import MatchResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    #await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# in-memory cache for prev matchings for now
matching_cache = dict()


async def merge_previous_assignments(input_df: pd.DataFrame, session: AsyncSession):
    '''Look up each participant in the database and populate Previously Assigned field'''

    for idx, row in input_df.iterrows():
        email = row['Email']

        # Query for this user's previous assignments
        query = select(PreviouslyAssigned).join(
            User, PreviouslyAssigned.recipient_id == User.id
        ).where(User.email == email)

        result = await session.execute(query)
        prev_assignments = result.scalars().all()

        # Get the emails of artists who have drawn for this person before
        if prev_assignments:
            prev_artist_query = select(User.email).where(
                User.id.in_([pa.artist_id for pa in prev_assignments])
            )
            prev_result = await session.execute(prev_artist_query)
            prev_emails = [email for email, in prev_result.all()]
            input_df.at[idx, 'Previously Assigned'] = ', '.join(prev_emails)
        else:
            input_df.at[idx, 'Previously Assigned'] = ''

    return input_df


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

        input_df = matching.form_response_to_input(temp_input.name)

        # merge with prev data
        input_df = await merge_previous_assignments(input_df, session)

        # Save processed input
        matching_id = str(uuid.uuid4())
        input_path = f'generated/input_{matching_id}.csv'
        input_df.to_csv(input_path, index = False)

        # attempt matching
        raw = [i[1] for i in input_df.iterrows()]
        artists = [matching.Artist(i) for i in raw]

        NUM_ATTEMPTS = 100
        for _ in range(NUM_ATTEMPTS):
            match_results = matching.run(artists)

            if match_results['success']:
                break

        # store in matching cache
        match_response = {
                'matching_id': matching_id,
                'success': match_results['success'],
                'matched_count': len(match_results['assignments']),
                'total_count': len(artists),
                'unmatched': [
        {'name': artist.name, 'email': artist.email, 'discord': artist.discord}
        for artist in match_results['failed']]
        }

        # cleaner way to do this
        matching_cache[matching_id] = {
                'success': match_results['success'],
                'confirmed': False,
                'matched_count': len(match_results['assignments']),
                'total_count': len(artists),
                'assignments': match_results['assignments'],
                'unmatched': [
        {'name': artist.name, 'email': artist.email, 'discord': artist.discord}
        for artist in match_results['failed']]
        }


        return match_response

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
    if matching_id not in matching_cache:
        raise HTTPException(status_code=404, detail = f'No such matching: {matching_id}')

    response = matching_cache[matching_id]
    response.pop('assignments')
    response['matching_id'] = matching_id

    edges = [{}]

    return response

@app.post('/matchings/{matching_id}/confirm')
async def confirm_matching(matching_id: str,
                           session: AsyncSession = Depends(get_async_session)):
    '''User confirms the matching. Matches are committed to the previously_assigned table.'''
    if matching_id not in matching_cache:
        raise HTTPException(status_code=404, detail = f'No such matching: {matching_id}')

    match_info = matching_cache[matching_id]

    # prevent double-confirmations
    if match_info['confirmed']:
        raise HTTPException(status_code=400, detail = 'This matching is already confirmed.')

    try:
        for artist, recipient in match_info['assignments']:

            artist_user = await session.execute(select(User).where(User.email == artist.email))
            recipient_user = await session.execute(select(User).where(User.email == recipient.email))

            artist_user = artist_user.scalar_one_or_none()
            recipient_user = recipient_user.scalar_one_or_none()

            # add artist to db if not already existing
            if not artist_user:
                artist_user = User(email=artist.email,
                                   name=artist.name,
                                   discord=artist.discord)
                session.add(artist_user)
                await session.flush() # to access id for insertion

            if not recipient_user:
                recipient_user = User(email=recipient.email,
                                      name=recipient.name,
                                      discord=recipient.discord)
                session.add(recipient_user)
                await session.flush()

            # add the assignment
            prev_assigned = PreviouslyAssigned(
                artist_id = artist_user.id,
                recipient_id = recipient_user.id
            )
            session.add(prev_assigned)
        await session.commit()
        match_info['confirmed'] = True

        return {'message': 'Matching confirmed successfully', 'matching_id': matching_id}


    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))



@app.get('/matchings/{matching_id}/download')
async def download_output(matching_id: str) -> FileResponse:
    ''' Returns output.csv file for download.'''
    if matching_id not in matching_cache:
        raise HTTPException(status_code=404, detail=f'No such matching: {matching_id}')

    assignment = matching_cache[matching_id]['assignments']

    output_path = f'generated/output_{matching_id}.csv'
    matching.export_to_csv(assignment, output_path)

    return FileResponse(output_path, media_type='text/csv')


