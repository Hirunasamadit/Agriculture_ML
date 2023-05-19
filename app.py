import os
from typing import List

import motor.motor_asyncio
import pandas as pd
from bson import ObjectId
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from similarity import find_similar_products

# show all columns
pd.set_option('display.max_columns', None)

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# load environment variables
from dotenv import load_dotenv

load_dotenv()

client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGODB_URL"])
db = client.agriculture

data_length = 10000

base_url = "http://localhost:8000/"
save_path = "data/"


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


# interaction
#     _id: { type: Schema.Types.ObjectId },
#     customerId: { type: Schema.Types.ObjectId, ref: "Customer" },
#     productId: { type: Schema.Types.ObjectId, ref: "Product" },
#     interactionType: { type: Number, enum: [1, 2, 3] }, // 1: click, 2: save, 3: unsave

# feedbacks
#    _id: { type: Schema.Types.ObjectId },
#    feedbackStarCount: { type: Number, enum: [1, 2, 3, 4, 5] },
#    customerId: { type: Schema.Types.ObjectId, ref: "Customer" },
#    sellerId: { type: Schema.Types.ObjectId, ref: "Seller" },

class FeedbacksModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    feedbackStarCount: int = Field(..., ge=1, le=5)
    customerId: str = Field(...)
    sellerId: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "_id": "5f9f1b9b0b9b9b9b9b9b9b9b",
                "feedbackStarCount": 5,
                "customerId": "5f9f1b9b0b9b9b9b9b9b9b9b",
                "sellerId": "5f9f1b9b0b9b9b9b9b9b9b9b"
            }
        }


# productCategories
#     _id: { type: Schema.Types.ObjectId },
#     productCatrgoryName: { type: String },

class ProductCategoriesModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    productCatrgoryName: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "_id": "5f9f1b9b0b9b9b9b9b9b9b9b",
                "productCatrgoryName": "Fruits",
            }
        }


# List all product categories
@app.get("/product-categories", response_description="List all product categories",
         response_model=List[ProductCategoriesModel])
async def list_product_categories():
    product_categories = await db["productCategories"].find().to_list(data_length)
    return product_categories


# products
#     _id: { type: Schema.Types.ObjectId },
#     productName: { type: String },
#     price: { type: Number },
#     productImage: { type: String },
#     description: { type: String },
#     productCatogoryId: { type: Schema.Types.ObjectId, ref: "ProductCategory" },
#     sellerId: { type: Schema.Types.ObjectId, ref: "Seller" },
#     availableQuantity: { type: Number },

class ProductsModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    productName: str = Field(...)
    price: float = Field(...)
    productImage: str = Field(...)
    description: str = Field(...)
    productCatogoryId: PyObjectId = Field(default_factory=PyObjectId)
    availableQuantity: int = Field(...)
    createdDate: str = Field()

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "_id": "5f9f1b9b0b9b9b9b9b9b9b9b",
                "productName": "Apple",
                "price": 1.99,
                "productImage": "https://www.google.com",
                "description": "A fruit",
                "productCatogoryId": "5f9f1b9b0b9b9b9b9b9b9b9b",
                "availableQuantity": 100,
                "createdDate": "2020-10-31"
            }
        }


# List all products
@app.get("/products", response_description="List all products", response_model=List[ProductsModel])
async def list_products():
    products = await db["products"].find().to_list(data_length)
    return products


def process():
    # load csv
    df = pd.read_csv(save_path + "aggregated.csv")

    # remove null values
    df.dropna(inplace=True)

    # remove duplicate values
    df.drop_duplicates(inplace=True)

    # save to csv
    df.to_csv(save_path + "processed.csv", index=False)


def aggregate_data():
    # load csv
    products = pd.read_csv(save_path + "products.csv")
    prodoutCategory = pd.read_csv(save_path + "prodoutCategory.csv")

    # merge dataframes products and prodoutCategory
    df = pd.merge(products, prodoutCategory, left_on="productCatogoryId", right_on="_id")

    # add index column
    df["index"] = df.index

    # save to csv
    df.to_csv(save_path + "aggregated.csv", index=False)


# Load data and Recommendation
@app.get("/recommendation/{user_id}")
async def get_recommendation(user_id: str, num_of_rec: int = 5):
    products = await db["products"].find().to_list(data_length)
    prodoutCategory = await db["productCategories"].find().to_list(data_length)

    products = pd.DataFrame(products)
    prodoutCategory = pd.DataFrame(prodoutCategory)

    products.to_csv(save_path + "products.csv", index=False)
    prodoutCategory.to_csv(save_path + "prodoutCategory.csv", index=False)

    aggregate_data()
    process()

    if num_of_rec:
        recommendation = find_similar_products(user_id, num_of_products=num_of_rec)
    else:
        recommendation = find_similar_products(user_id, num_of_products=5)
    return {"recommendations": recommendation}


# Load data
@app.get("/load-data")
async def load_data(request: Request):
    products = await db["products"].find().to_list(data_length)
    prodoutCategory = await db["productCategories"].find().to_list(data_length)

    products = pd.DataFrame(products)
    prodoutCategory = pd.DataFrame(prodoutCategory)

    products.to_csv(save_path + "products.csv", index=False)
    prodoutCategory.to_csv(save_path + "prodoutCategory.csv", index=False)

    aggregate_data()
    process()

    return {"status": "success"}
