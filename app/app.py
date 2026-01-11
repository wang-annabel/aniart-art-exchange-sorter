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
from app.schemas import MatchResponse, FileUploadResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    #await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# in-memory caches
uploaded_files_cache = dict()
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


@app.post('/files/upload')
async def upload_file(
        file: UploadFile = File(...),
        session: AsyncSession = Depends(get_async_session)
) -> FileUploadResponse:
    '''
    Upload and process a CSV file. Returns a file_id that can be used
    to create matchings.
    '''
    temp_input = tempfile.NamedTemporaryFile(delete = False,
                                             suffix = os.path.splitext(file.filename)[1])

    try:
        # Save uploaded file
        shutil.copyfileobj(file.file, temp_input)
        temp_input.close()

        # Convert to input format
        input_df = matching.form_response_to_input(temp_input.name)

        # Merge with previous assignments
        input_df = await merge_previous_assignments(input_df, session)

        # Generate file ID and cache the processed DataFrame
        file_id = str(uuid.uuid4())
        uploaded_files_cache[file_id] = {
            'dataframe': input_df,
            'filename': file.filename,
            'participant_count': len(input_df)
        }

        # Optionally save to disk for persistence
        input_path = f'generated/input_{file_id}.csv'
        input_df.to_csv(input_path, index = False)

        return {
            'file_id': file_id,
            'filename': file.filename,
            'participant_count': len(input_df)
        }

    except TypeError:
        raise HTTPException(status_code = 400,
                            detail = 'Invalid file type. Please upload a CSV file.')
    except KeyError as e:
        raise HTTPException(status_code = 422,
                            detail = f'Invalid CSV format. Missing required column {str(e)}')
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))
    finally:
        if temp_input.name and os.path.exists(temp_input.name):
            os.unlink(temp_input.name)
        file.file.close()

@app.post('/matchings')
async def create_matching(file_id: str) -> MatchResponse:
    '''
    Create a new matching from a previously uploaded file.
    Can be called multiple times with the same file_id to generate different matchings.
    '''
    # verify file exists
    if file_id not in uploaded_files_cache:
        raise HTTPException(status_code=404, detail=f'No uploaded file found with id: {file_id}')

    try:
        # Get the cached DataFrame
        file_data = uploaded_files_cache[file_id]
        input_df = file_data['dataframe']

        # Convert to Artist objects
        raw = [i[1] for i in input_df.iterrows()]
        artists = [matching.Artist(i) for i in raw]

        # Run matching algorithm
        NUM_ATTEMPTS = 100
        match_results = None
        for _ in range(NUM_ATTEMPTS):
            match_results = matching.run(artists)
            if match_results['success']:
                break

        # Generate matching ID
        matching_id = str(uuid.uuid4())

        # Cache the matching results
        matching_cache[matching_id] = {
            'file_id': file_id,  # Link back to source file
            'success': match_results['success'],
            'confirmed': False,
            'matched_count': len(match_results['assignments']),
            'total_count': len(artists),
            'assignments': match_results['assignments'],
            'unmatched': [
                {'name': artist.name, 'email': artist.email, 'discord': artist.discord}
                for artist in match_results['failed']
            ]
        }

        # Return response
        return {
            'matching_id': matching_id,
            'file_id': file_id,
            'success': match_results['success'],
            'matched_count': len(match_results['assignments']),
            'total_count': len(artists),
            'unmatched': matching_cache[matching_id]['unmatched']
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/matchings/{matching_id}')
async def get_matching(matching_id: str):
    '''Returns details of a matching attempt.
    Returns data for a graph visualization'''
    if matching_id not in matching_cache:
        raise HTTPException(status_code=404, detail = f'No such matching: {matching_id}')

    response = matching_cache[matching_id]
    assignments = response['assignments']
    # response.pop('assignments')
    # response['matching_id'] = matching_id

    # Build nodes and links
    nodes_dict = {}
    links = []

    for artist, recipient in assignments:
        # Add nodes
        if artist.email not in nodes_dict:
            nodes_dict[artist.email] = {
                'id': artist.email,
                'name': artist.name,
                'discord': artist.discord,
                'email': artist.email
            }
        if recipient.email not in nodes_dict:
            nodes_dict[recipient.email] = {
                'id': recipient.email,
                'name': recipient.name,
                'discord': recipient.discord,
                'email': recipient.email
            }

        # Add link (artist draws for recipient)
        links.append({
            'source': artist.email,
            'target': recipient.email
        })

    return {
        'nodes': list(nodes_dict.values()),
        'links': links
    }



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


