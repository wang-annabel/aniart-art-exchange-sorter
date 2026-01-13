# app/app.py

from fastapi import FastAPI, HTTPException, File, UploadFile, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
import tempfile
import pandas as pd
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db import (
    create_db_and_tables,
    get_async_session,
    User,
    Participant,
    PreviouslyAssigned,
    Matching
)
import app.matching as matching
from app.graph import cycles
from app.schemas import (
    MatchResponse,
    FileUploadResponse,
    GraphResponse,
    UserRead,
    UserCreate
)
from app.users import auth_backend, fastapi_users, current_active_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan = lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],  # Adjust for production
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

# In-memory caches
uploaded_files_cache = dict()  # file_id -> processed DataFrame
matching_cache = dict()  # matching_id -> matching results

# ============================================================================
# Authentication Routes
# ============================================================================

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix = "/auth/jwt",
    tags = ["auth"]
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix = "/auth",
    tags = ["auth"]
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserCreate),
    prefix = "/users",
    tags = ["users"]
)


# ============================================================================
# Helper Functions
# ============================================================================

async def merge_previous_assignments(input_df: pd.DataFrame, session: AsyncSession):
    '''Look up each participant in the database and populate Previously Assigned field'''
    for idx, row in input_df.iterrows():
        email = row['Email']

        # Query for this participant's previous assignments
        query = select(PreviouslyAssigned).join(
            Participant, PreviouslyAssigned.recipient_id == Participant.id
        ).where(Participant.email == email)

        result = await session.execute(query)
        prev_assignments = result.scalars().all()

        # Get the emails of artists who have drawn for this person before
        if prev_assignments:
            prev_artist_query = select(Participant.email).where(
                Participant.id.in_([pa.artist_id for pa in prev_assignments])
            )
            prev_result = await session.execute(prev_artist_query)
            prev_emails = [email for email, in prev_result.all()]
            input_df.at[idx, 'Previously Assigned'] = ', '.join(prev_emails)
        else:
            input_df.at[idx, 'Previously Assigned'] = ''

    return input_df


# Optional user dependency - returns None if not authenticated
async def get_optional_user(
        user: User = Depends(fastapi_users.current_user(optional = True))
) -> Optional[User]:
    return user


# ============================================================================
# File Upload Routes (No auth required)
# ============================================================================

@app.post('"/files/upload"')
async def upload_file(
        file: UploadFile = File(...),
        session: AsyncSession = Depends(get_async_session),
        user: Optional[User] = Depends(get_optional_user)
) -> FileUploadResponse:
    '''Upload and process a CSV file. Returns a file_id that can be used to create matchings.
    Authentication is optional - logged in users can track their uploads.'''
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
            'participant_count': len(input_df),
            'uploaded_by': user.id if user else None  # Track if logged in
        }

        # Optionally save to disk for persistence
        input_path = f'generated/input_{file_id}.csv'
        os.makedirs('generated', exist_ok = True)
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


@app.get('/files/{file_id}')
async def get_file_info(file_id: str):
    '''Get information about an uploaded file. No authentication required.'''
    if file_id not in uploaded_files_cache:
        raise HTTPException(status_code = 404, detail = f'No file found with id: {file_id}')

    file_data = uploaded_files_cache[file_id]
    return {
        'file_id': file_id,
        'filename': file_data['filename'],
        'participant_count': file_data['participant_count']
    }


# ============================================================================
# Matching Routes (No auth required for create/view/download)
# ============================================================================

@app.post('/matchings')
async def create_matching(
        file_id: str,
        user: Optional[User] = Depends(get_optional_user)
) -> MatchResponse:
    '''Create a new matching from a previously uploaded file.
    Authentication is optional; logged in users can track their matchings.'''
    if file_id not in uploaded_files_cache:
        raise HTTPException(status_code = 404,
                            detail = f'No uploaded file found with id: {file_id}')

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
            'file_id': file_id,
            'created_by': user.id if user else None,  # Track if logged in
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

        return {
            'matching_id': matching_id,
            'file_id': file_id,
            'success': match_results['success'],
            'matched_count': len(match_results['assignments']),
            'total_count': len(artists),
            'unmatched': matching_cache[matching_id]['unmatched']
        }

    except Exception as e:
        print(str(e))
        raise HTTPException(status_code = 500, detail = str(e))


@app.get('/matchings/{matching_id}')
async def get_matching(matching_id: str) -> GraphResponse:
    '''Returns details of a matching attempt with graph visualization data.
    No authentication required.'''
    if matching_id not in matching_cache:
        raise HTTPException(status_code = 404, detail = f'No such matching: {matching_id}')

    response = matching_cache[matching_id]
    assignments = response['assignments']

    # Build nodes and links
    nodes_dict = {}
    links = []

    for artist, recipient in assignments:
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

        links.append({
            'source': artist.email,
            'target': recipient.email
        })

    nodes = list(nodes_dict.values())
    node_ids = [node['id'] for node in nodes]

    return {
        'matching_id': matching_id,
        'nodes': nodes,
        'links': links,
        'participants': len(nodes_dict),
        'cycles': cycles(node_ids, links),
        'unmatched': len(response['unmatched'])
    }


@app.get('/matchings/{matching_id}/download')
async def download_output(matching_id: str) -> FileResponse:
    '''Returns output.csv file for download. No authentication required.'''
    if matching_id not in matching_cache:
        raise HTTPException(status_code = 404, detail = f'No such matching: {matching_id}')

    assignment = matching_cache[matching_id]['assignments']
    output_path = f'generated/output_{matching_id}.csv'
    os.makedirs('generated', exist_ok = True)
    matching.export_to_csv(assignment, output_path)

    return FileResponse(
        output_path,
        media_type = 'text/csv',
        filename = f'matching_{matching_id}.csv'
    )


# ============================================================================
# Confirm Matching (REQUIRES authentication)
# ============================================================================

@app.post('/matchings/{matching_id}/confirm')
async def confirm_matching(
        matching_id: str,
        user: User = Depends(current_active_user),  # ← Authentication REQUIRED
        session: AsyncSession = Depends(get_async_session)
):
    '''Confirm the matching and commit to database.
    **Authentication required** - only logged in users can confirm matchings.'''
    if matching_id not in matching_cache:
        raise HTTPException(status_code = 404, detail = f'No such matching: {matching_id}')

    match_info = matching_cache[matching_id]

    if match_info['confirmed']:
        raise HTTPException(status_code = 400, detail = 'This matching is already confirmed.')

    try:
        # Create Matching record
        matching_record = Matching(
            id = uuid.UUID(matching_id),
            created_by = user.id,
            file_id = match_info['file_id'],
            participant_count = match_info['total_count']
        )
        session.add(matching_record)
        await session.flush()

        # Create participant records and assignments
        for artist, recipient in match_info['assignments']:
            # Get or create artist participant
            artist_participant = await session.execute(
                select(Participant).where(Participant.email == artist.email)
            )
            artist_participant = artist_participant.scalar_one_or_none()

            if not artist_participant:
                artist_participant = Participant(
                    email = artist.email,
                    name = artist.name,
                    discord = artist.discord
                )
                session.add(artist_participant)
                await session.flush()

            # Get or create recipient participant
            recipient_participant = await session.execute(
                select(Participant).where(Participant.email == recipient.email)
            )
            recipient_participant = recipient_participant.scalar_one_or_none()

            if not recipient_participant:
                recipient_participant = Participant(
                    email = recipient.email,
                    name = recipient.name,
                    discord = recipient.discord
                )
                session.add(recipient_participant)
                await session.flush()

            # Create assignment
            prev_assigned = PreviouslyAssigned(
                artist_id = artist_participant.id,
                recipient_id = recipient_participant.id,
                matching_id = matching_record.id
            )
            session.add(prev_assigned)

        await session.commit()
        match_info['confirmed'] = True

        return {
            'message': 'Matching confirmed successfully',
            'matching_id': matching_id
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code = 500, detail = str(e))


# ============================================================================
# User History Routes (REQUIRES authentication)
# ============================================================================

@app.get('/my-matchings')
async def get_my_matchings(
        user: User = Depends(current_active_user),  # ← Authentication REQUIRED
        session: AsyncSession = Depends(get_async_session)
):
    '''Get all confirmed matchings created by the current user.
    **Authentication required**.'''
    query = select(Matching).where(Matching.created_by == user.id).order_by(
        Matching.created_at.desc())
    result = await session.execute(query)
    matchings = result.scalars().all()

    return {
        'matchings': [
            {
                'matching_id': str(m.id),
                'created_at': m.created_at.isoformat(),
                'participant_count': m.participant_count,
                'file_id': m.file_id
            }
            for m in matchings
        ]
    }


@app.get('/me')
async def get_current_user(user: User = Depends(current_active_user)):
    '''Get current logged in user info. **Authentication required**.'''
    return {
        'id': str(user.id),
        'email': user.email,
        'name': user.name,
        'is_active': user.is_active,
        'is_verified': user.is_verified
    }