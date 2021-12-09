import re
import os
from typing import Optional, List, Dict

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from scripts import parse_universities, get_brief_univers_data

app = FastAPI(title="UniParser")


@app.get("/univerdata/")
async def parse_specialities(region: Optional[str] = None,
                       city: Optional[str] = None,
                       field: Optional[str] = None,
                       speciality: Optional[str] = None):

    if field:
        if re.match("([0-9]+)", field) is not None:
            field = int(re.match("([0-9]+)", field).group(0))
    if speciality:
        if re.match("([0-9]+)", speciality) is not None:
            speciality = re.match("([0-9]+)", speciality).group(0)

    try:
        response = await parse_universities(region, city, field, speciality)
        return JSONResponse(response)
    except ValueError as e:
        return e


@app.post("/favourites/")
async def parse_favs(request: Request):
    data = await request.json()
    univers = data.get('univers')
    response = await get_brief_univers_data(univers)
    return JSONResponse(response)


if __name__ == '__main__':
    uvicorn.run(app, port=os.environ.get('PORT', 8080), host='localhost')

# uvicorn main:app --reload