from flask import Blueprint, request, abort, make_response
from ..db import db
from ..models.pet import Pet
from google import genai

client = genai.Client()

bp = Blueprint("pets", __name__, url_prefix="/pets")

@bp.post("")
def create_pet():
    request_body = request.get_json()
    try:
        new_pet = Pet.from_dict(request_body)
        db.session.add(new_pet)
        db.session.commit()

        return new_pet.to_dict(), 201

    except KeyError as e:
        abort(make_response({"message": f"missing required value: {e}"}, 400))

@bp.get("")
def get_pets():
    pet_query = db.select(Pet)

    pets = db.session.scalars(pet_query)
    response = []

    for pet in pets:
        response.append(pet.to_dict())

    return response

@bp.get("/<pet_id>")
def get_single_pet(pet_id):
    pet = validate_model(Pet,pet_id)
    return pet.to_dict()

def validate_model(cls,id):
    try:
        id = int(id)
    except:
        response =  response = {"message": f"{cls.__name__} {id} invalid"}
        abort(make_response(response , 400))

    query = db.select(cls).where(cls.id == id)
    model = db.session.scalar(query)
    if model:
        return model

    response = {"message": f"{cls.__name__} {id} not found"}
    abort(make_response(response, 404))

@bp.get("/<pet_id>/names")
def get_names(pet_id):
    pet = validate_model(Pet, pet_id)
    response = [name.to_dict() for name in pet.names]

    return response

@bp.post("/<pet_id>/generate")
def add_names(pet_id):
    pet_obj = validate_model(Pet, pet_id)

    if pet_obj.names:
        return {"message": f"Names already generated for {pet_obj.name} "}, 201

    names = generate_names(pet_obj)

    new_names = []

    for name in names:
        new_name = Pet(
            name_text=name,
            pet=pet_obj
        )
        new_names.append(new_name)

    db.session.add_all(new_names)
    db.session.commit()

def generate_names(pet):
    input_message = f"I have a {pet.color} {pet.animal_type} who has a {pet.personality} personality. Please suggest a list of 5 names for this pet."
    response = client.models.generate_content(
        model="gemini-3.5-flash", contents=input_message
    )
    lines = response.text.splitlines()
    return [line.strip("\"',") for line in lines]