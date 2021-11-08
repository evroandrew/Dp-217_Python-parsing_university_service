import re
from json import JSONDecodeError
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from scripts import main

app = FastAPI(title="UniParser")


@app.get("/univerdata/")
def parse_specialities(region: Optional[str] = None,
                       city: Optional[str] = None,
                       field: Optional[str] = None,
                       speciality: Optional[str] = None):

    if field:
        if re.match("([0-9]+)", field) is not None:
            field = int(re.match("([0-9]+)", field).group(0))
    if speciality:
        if re.match("([0-9]+)", speciality) is not None:
            speciality = re.match("([0-9]+)", speciality).group(0)

    print(f"reg {region}, city {city}, field {field}, spec {speciality}")
    try:
        response = main(region, city, field, speciality)
        return JSONResponse(response)
    except ValueError as e:
        return e